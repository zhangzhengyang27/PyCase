"""示例导入核心：目录中真实 .py → JSON 集合 payload 的纯内存构建。

单一实现供两个调用方复用（防止逻辑分叉）：
- sidecar RPC ``import_examples``（应用内导入向导；PyInstaller 打包须包含本模块，
  因此逻辑必须位于 ``app/`` 包而非 ``scripts/``）
- ``scripts/migrate_to_json.py``（CLI 批量迁移薄壳，仅保留编排与写盘）

导入产物**不写 ``dir`` 字段**：用户目录没有稳定仓库根，运行时走单文件物化
（同目录兄弟模块暂不解析，限制见 docs/json-examples.md）。
"""

import ast
import re
import warnings
from pathlib import Path

from .logger import get_logger

# 合法 PyPI 包名（不含版本约束部分）；非法名（乱码/无效导入）在依赖合并前被丢弃
VALID_PKG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")

SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}

TAG_BY_MODULE = {
    "requests": "网络",
    "urllib": "网络",
    "socket": "网络",
    "http": "网络",
    "sqlite3": "数据库",
    "sqlalchemy": "数据库",
    "pymongo": "数据库",
    "tkinter": "GUI",
    "PyQt": "GUI",
    "PySide": "GUI",
    "matplotlib": "可视化",
    "seaborn": "可视化",
    "plotly": "可视化",
    "numpy": "数据科学",
    "pandas": "数据科学",
    "asyncio": "并发",
    "threading": "并发",
    "multiprocessing": "并发",
    "unittest": "测试",
    "pytest": "测试",
    "flask": "Web",
    "django": "Web",
    "fastapi": "Web",
}

# 顶层 import 名 -> PyPI 包名 的常见映射（其余回退为 import 名本身）
IMPORT_TO_PKG = {
    "mpl_toolkits": "matplotlib",
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "wx": "wxPython",
    "lxml": "lxml",
    "Crypto": "pycryptodome",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "PyQt5": "PyQt5",
    "PyQt6": "PyQt6",
    "PySide2": "PySide2",
    "PySide6": "PySide6",
    "pytesseract": "pytesseract",
    "xlrd": "xlrd",
    "openpyxl": "openpyxl",
    "pymysql": "PyMySQL",
    "psycopg2": "psycopg2-binary",
    "mysql": "mysql-connector-python",
    "pymongo": "pymongo",
    "redis": "redis",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "keras": "keras",
    "scipy": "scipy",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "dash": "dash",
    "streamlit": "streamlit",
    "gradio": "gradio",
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "tornado": "tornado",
    "aiohttp": "aiohttp",
    "requests": "requests",
    "httpx": "httpx",
    "urllib3": "urllib3",
    "nltk": "nltk",
    "spacy": "spacy",
    "gensim": "gensim",
    "wordcloud": "wordcloud",
    "matplotlib": "matplotlib",
    "pandas": "pandas",
    "numpy": "numpy",
    "sqlalchemy": "SQLAlchemy",
    "playwright": "playwright",
    "selenium": "selenium",
    "pyautogui": "pyautogui",
    "speechrecognition": "SpeechRecognition",
    "gtts": "gTTS",
    "pydub": "pydub",
    "fpdf": "fpdf",
    "reportlab": "reportlab",
    "weasyprint": "WeasyPrint",
    "markdown": "Markdown",
    "jinja2": "Jinja2",
    "xlsxwriter": "xlsxwriter",
    "altair": "altair",
    "networkx": "networkx",
    "face_recognition": "face-recognition",
    "dlib": "dlib",
    "imutils": "imutils",
    "skimage": "scikit-image",
    "requests_cache": "requests-cache",
    "undetected_chromedriver": "undetected-chromedriver",
    "pdfkit": "pdfkit",
    "jenkins": "python-jenkins",
    "ddddocr": "ddddocr",
    "allure": "allure-pytest",
    "sshtunnel": "sshtunnel",
    "yagmail": "yagmail",
    "pydocx": "python-docx",
    "dbutils": "dbutils",
    "splinter": "splinter",
    "pykeyboard": "pykeyboard",
    "aircv": "aircv",
    "aip": "baidu-aip",
    "xlwt": "xlwt",
    "valley": "valley",
}


def slugify(text: str) -> str:
    """生成安全的示例 id（仅字母数字 - _ .）。"""
    text = text.replace(" ", "_")
    return re.sub(r"[^0-9A-Za-z_.-]", "_", text)


def extract_imports(code: str) -> set[str]:
    """AST 解析代码的顶层导入模块名（老示例常见非法转义，抑制 SyntaxWarning）。"""
    mods: set[str] = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return mods
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
    return mods


def derive_tags(rel_parts: list[str], imports: set[str]) -> list[str]:
    """目录层级标签（首尾段除外）+ import 模块的中文分类标签，排序去重。"""
    tags: set[str] = set()
    for part in rel_parts[1:-1]:
        tags.add(part)
    for mod in imports:
        for key, tag in TAG_BY_MODULE.items():
            if key.lower() in mod.lower():
                tags.add(tag)
    return sorted(t for t in tags if t)


def read_requirements(pkg_dir: Path, source_root: Path | None = None) -> list[str]:
    """读示例目录（沿父目录向上查到源根）的 requirements.txt，返回包名列表（兼容 UTF-16/UTF-8，剥离版本约束）。"""
    req = next(
        (
            d / "requirements.txt"
            for d in [pkg_dir, *pkg_dir.parents]
            if (d / "requirements.txt").exists()
            and (
                source_root is None
                or d == source_root
                or d in source_root.parents
                or d.is_relative_to(source_root)
            )
        ),
        None,
    )
    if req is None:
        return []
    try:
        raw = req.read_bytes()
    except OSError:
        return []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", errors="ignore")
    else:
        text = raw.decode("utf-8", errors="ignore")
    names: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        name = re.split(r"[<>=!~;\s\[]", line, maxsplit=1)[0].strip()
        if name and VALID_PKG_RE.match(name):
            names.append(name)
    return names


def default_is_available(mod: str) -> bool:
    """当前运行环境是否已能导入该顶层模块（标准库或已安装）。"""
    import importlib.util

    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return True  # 探测失败按可用处理（宁可少猜不误删）


def guess_requirements(
    code: str,
    local_modules: set[str],
    is_available=None,
) -> list[str]:
    """从代码猜测缺失的第三方依赖，返回 PyPI 包名列表（按 import 名排序，保持确定性）。

    - 已可导入（标准库/已安装）的不计；
    - 属于源目录本地模块的不计（由物化/运行路径解析——导入场景暂不解析兄弟模块，
      此处仍排除以免把用户目录里的公共模块误判为 PyPI 包）；
    - 其余经 IMPORT_TO_PKG 映射（缺失回退 import 名）。
    """
    if is_available is None:
        is_available = default_is_available
    pkgs: list[str] = []
    for mod in sorted(extract_imports(code)):
        if is_available(mod):
            continue
        if mod in local_modules:
            continue
        pkg = IMPORT_TO_PKG.get(mod, mod).strip()
        if pkg and pkg not in pkgs and VALID_PKG_RE.match(pkg):
            pkgs.append(pkg)
    return pkgs


def build_source_modules(source: Path) -> set[str]:
    """扫描源目录，收集可作为本地模块的顶层名（.py 文件名、包目录、祖先目录）。

    这些模块靠运行期路径解析，不应被当作第三方包去 pip 安装。
    """
    names: set[str] = set()
    try:
        entries = list(source.rglob("*.py"))
    except OSError:
        return names
    for p in entries:
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name == "__init__.py":
            names.add(p.parent.name)
        else:
            names.add(p.stem)
        cur = p.parent
        while cur != source and cur != cur.parent:
            names.add(cur.name)
            cur = cur.parent
    return names


def ensure_unique_id(base_id: str, seen_ids: set[str]) -> str:
    """id 去重：冲突时追加 _2/_3 后缀（与既有迁移数据口径一致）。"""
    example_id = base_id
    n = 1
    while example_id in seen_ids:
        n += 1
        example_id = f"{base_id}_{n}"
    seen_ids.add(example_id)
    return example_id


def describe_from_readme(py_file: Path, source_root: Path | None = None) -> str:
    """README.md 首行（去 # 前缀）作为描述。

    从示例所在目录沿父目录向上查找，直到源根（不含源根之上）；
    找不到 README 或读取失败返回空串。
    """
    for d in [py_file.parent, *py_file.parents]:
        readme = d / "README.md"
        if readme.exists():
            try:
                lines = readme.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                return ""
            return lines[0].lstrip("#").strip() if lines else ""
        if source_root is not None and d == source_root:
            break
    return ""


def spec_from_file(
    py_file: Path,
    source_root: Path,
    source_modules: set[str],
    *,
    category: str = "user",
    is_available=None,
    seen_ids: set[str] | None = None,
) -> dict:
    """单个 .py 文件 → 示例 spec（不写 dir：用户集合走单文件物化）。"""
    code = py_file.read_text(encoding="utf-8", errors="ignore")
    rel = py_file.relative_to(source_root).as_posix()
    rel_parts = rel.split("/")
    imports = extract_imports(code)
    if seen_ids is None:
        seen_ids = set()
    example_id = ensure_unique_id(slugify(rel), seen_ids)
    declared = read_requirements(py_file.parent, source_root)
    guessed = guess_requirements(code, source_modules, is_available=is_available)
    merged = list(dict.fromkeys(declared + guessed))
    return {
        "id": example_id,
        "name": py_file.name,
        "category": category,
        "tags": derive_tags(rel_parts, imports),
        "description": describe_from_readme(py_file, source_root),
        "requirements": merged,
        "code": code,
    }


def import_directory(
    source: Path,
    name: str,
    *,
    existing_ids: set[str] | None = None,
    is_available=None,
) -> dict:
    """把源目录下全部 .py（跳过 SKIP_DIRS 与隐藏目录）构建为一个用户集合 payload。

    纯内存构建、不写盘；id 对 ``existing_ids``（内置库 + 已有用户集合）与本批内
    双重去重。返回 ``{"name", "description", "examples", "skipped", "stats"}``，
    ``skipped`` 为 ``[{"file", "reason"}]``（空文件/读取失败等）。
    """
    existing = set(existing_ids or ())
    seen_ids: set[str] = set(existing)
    source_modules = build_source_modules(source)
    examples: list[dict] = []
    skipped: list[tuple[str, str]] = []
    try:
        py_files = sorted(source.rglob("*.py"))
    except OSError as e:
        get_logger(__name__).error("扫描导入目录失败 %s: %s", source, e)
        py_files = []
    for py_file in py_files:
        rel = py_file.relative_to(source).as_posix()
        if any(part in SKIP_DIRS or part.startswith(".") for part in py_file.parts):
            skipped.append({"file": rel, "reason": "位于缓存/隐藏目录"})
            continue
        try:
            if not py_file.read_text(encoding="utf-8", errors="ignore").strip():
                skipped.append({"file": rel, "reason": "空文件"})
                continue
            spec = spec_from_file(
                py_file,
                source,
                source_modules,
                category="user",
                is_available=is_available,
                seen_ids=seen_ids,  # 全局去重：内置库 + 已有用户集合 + 本批
            )
        except OSError as e:
            skipped.append({"file": rel, "reason": f"读取失败: {e}"})
            continue
        examples.append(spec)
    return {
        "name": name,
        "description": f"导入自 {source.name} 的用户示例集合。",
        "examples": examples,
        "skipped": skipped,
        "stats": {
            "scanned": len(py_files),
            "imported": len(examples),
            "skipped": len(skipped),
        },
    }
