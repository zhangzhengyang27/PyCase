"""汇总全项目共享依赖清单：生成仓库根 requirements.txt。

设计模型：本项目是一个应用（一个项目、一份共享 .venv），json_examples 里的
全部示例只是它的模块——依赖在项目级声明一次，不在模块间各自为政。

数据来源（三层递进，均可缺省）：
1. json_examples/*.json 中各示例声明的 ``requirements`` 字段（PyPI 包名）
2. topics/tools/projects 原始仓库中的 requirements.txt（取包名部分，忽略版本约束）
3. **全部示例代码的实际 import 分析**：JSON 内联代码 + 原始仓库 .py 文件，
   排除标准库与仓库本地模块后，经 IMPORT_TO_PKG 映射（复用 migrate_to_json.py）
   得到真实需要的第三方包——历史数据中大多数示例并未声明 requirements，
   只有分析实际 import 才能保证清单完整。

非法包名（如历史迁移数据中的 UTF-16 乱码）会被过滤；输出经 PEP 503 规范化
去重、不锁版本（共享环境中一律安装最新兼容版）。

用法：python scripts/gen_shared_requirements.py
"""

import ast
import json
import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "requirements.txt"
sys.path.insert(0, str(ROOT))
from app.importer import IMPORT_TO_PKG, extract_imports  # noqa: E402  导入分析单一来源

# 合法 PyPI 包名（不含版本约束部分）
VALID_PKG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")

# 仓库本地模块/目录名（由 PYTHONPATH 解析，不是 PyPI 包）
LOCAL_MODULES = {
    "app",
    "common",
    "utils",
    "config",
    "items",
    "settings",
    "middlewares",
    "pipelines",
    "jobs",
    "opencourse",
    "topics",
    "tools",
    "projects",
}

SCAN_SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".json_examples_cache",
    ".desktop-app-venvs",
}

# 在当前 Python（3.14）上无 wheel 且源码编译必然失败的死包，显式排除：
# - pycrypto：2014 年起停止维护，现代编译器/Python 无法构建（示例应改用 pycryptodome）
# - typed-ast：已废弃，官方仅支持到 3.12 之前
# - pyqt5：GUI 框架，本应用无显示环境（GUI 示例本就无法交互运行），且该 Python 无 wheel
# - autotest：Python 2 时代的同名气包，源码构建必败
# - c01 / c1104 / corner-widget / tencentyoutuyun：原仓库源码中的无效导入名，PyPI 不存在
EXCLUDED_PKGS = {"pycrypto", "typed-ast", "pyqt5", "autotest", "c01", "c1104", "corner-widget", "tencentyoutuyun"}


def normalize(name: str) -> str:
    """PEP 503 规范化：大小写与 -_. 分隔符等价，Flask/flask 视为同一个包。"""
    return re.sub(r"[-_.]+", "-", name).lower()


def read_requirements_txt(path: Path) -> list[str]:
    """读取 requirements.txt（兼容 UTF-16/UTF-8），返回包名列表。"""
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", errors="ignore")
    else:
        text = raw.decode("utf-8", errors="ignore")
    names = []
    for line in text.splitlines():
        name = re.split(r"[<>=!~;\s\[]", line.strip(), maxsplit=1)[0].strip()
        if name and name not in LOCAL_MODULES and VALID_PKG_RE.match(name):
            names.append(name)
    return names


def build_local_modules() -> set[str]:
    """扫描仓库收集本地顶层模块名（.py 文件名、包/代码目录），避免误当第三方包。

    运行器会把示例目录及其祖先目录都加入 PYTHONPATH，因此仓库内任意
    .py 文件名与含 .py 的目录名都是可解析的本地模块。
    """
    local = set(LOCAL_MODULES)
    for base in ("topics", "tools", "projects", "app"):
        root = ROOT / base
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if any(part in SCAN_SKIP_DIRS for part in p.parts):
                continue
            if p.is_file() and p.suffix == ".py":
                local.add(p.stem)
            elif p.is_dir() and any(x.suffix == ".py" for x in p.iterdir()):
                local.add(p.name)
    return local


def collect() -> list[str]:
    pkgs: dict[str, None] = {}  # 规范化名 -> 占位，保持首次出现顺序
    local = build_local_modules()
    stdlib = sys.stdlib_module_names

    def add(name: str) -> None:
        name = name.strip()
        if not name:
            return
        norm = normalize(name)
        # 排除检查使用规范化名称（大小写不敏感、分隔符等价），
        # 避免 "PyQt5" 因大小写不同而绕过 EXCLUDED_PKGS 中的 "pyqt5"
        if norm in {normalize(m) for m in LOCAL_MODULES} or norm in {normalize(e) for e in EXCLUDED_PKGS}:
            return
        if not VALID_PKG_RE.match(name):
            return
        pkgs.setdefault(norm, None)

    def add_imports(code: str) -> None:
        for mod in extract_imports(code):
            if mod in stdlib or mod in local:
                continue
            add(IMPORT_TO_PKG.get(mod, mod))

    # 1) 示例声明的 requirements
    for json_file in (ROOT / "json_examples").glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"⚠ 跳过无法读取的集合 {json_file.name}: {e}", file=sys.stderr)
            continue
        for spec in data.get("examples", []):
            for r in spec.get("requirements") or []:
                add(str(r))
            # 3) 示例代码的实际 import（JSON 为唯一代码源）
            add_imports(spec.get("code", ""))

    # 2) 原始仓库 requirements.txt
    for base in ("topics", "tools", "projects"):
        for req in (ROOT / base).rglob("requirements.txt"):
            for name in read_requirements_txt(req):
                add(name)

    # 3) 原始仓库 .py 的实际 import（兄弟模块/未迁移文件也可能被示例导入）
    for base in ("topics", "tools", "projects"):
        root = ROOT / base
        if not root.is_dir():
            continue
        for py in root.rglob("*.py"):
            if any(part in SCAN_SKIP_DIRS for part in py.parts):
                continue
            try:
                code = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            add_imports(code)

    return sorted(pkgs)


def main() -> None:
    pkgs = collect()
    lines = [
        "# 全项目共享依赖清单（自动生成，勿手改）：python scripts/gen_shared_requirements.py",
        "# 模型：本项目是一个应用，json_examples 里的示例是它的模块；",
        "# 共享 .venv 首次创建时由 venv_manager 按本清单安装。",
        "",
        *pkgs,
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 已生成 {len(pkgs)} 个共享依赖 → {OUT}")


if __name__ == "__main__":
    main()
