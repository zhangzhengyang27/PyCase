"""派生事实的烘焙索引（契约 §3.2）。

派生事实是**只依赖文件内容的确定性函数**，因此在构建期烘焙、随包分发，
启动时以逐文件哈希校验替代重算；失配才全量重算一次并写缓存根。

烘焙的字段（每个条目）：
- ``file`` / ``size`` / ``sha256``：真实文件身份与内容哈希（校验用）；
- ``imports``：第三方 import 清单（与渲染层 FilterEngine.extractImportTags 同口径）；
- ``deps``：缺依赖判定用模块名（额外排除本地兄弟模块，与 ``third_party_imports`` 同口径）；
- ``quality`` / ``risk_high`` / ``risk_findings``：质量分与 HIGH 风险明细（运行前确认弹窗同源）；
- ``static``：静态可运行性状态（broken/empty/risky/runnable/unknown）；
- ``theme``：命中的主题 key（与渲染层 themes.ts 谓词同口径）。

**不烘焙** ``run_status`` 的缺依赖维度：它依赖运行环境（共享 venv 的模块索引），
运行时以「静态事实 + 模块索引」廉价合成（优先 broken/empty，再看缺失模块）。

本模块只做计算与校验（纯函数 + 字典），文件读写由 ``ContractStore`` 负责。
"""

import hashlib
import re
import json
import time
from pathlib import Path
from typing import Any

from .run_status import BROKEN, EMPTY, UNKNOWN, compute_run_status, parse_code, third_party_imports

SCHEMA_VERSION = 2
# facts 规则版本：评分规则 / 安全规则 / 静态状态 / 主题谓词任一变更即递增，
# 旧烘焙文件随即失效（头部版本比对），不会把旧规则的结果当成事实用。
FACTS_RULES_VERSION = 1
FACTS_FILENAME = "facts.json"

# 合法 PyPI 包名（剥离版本约束后）
VALID_PKG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")

# 静态状态里"无需再过缺依赖维度"的终态（与 compute_run_status 的优先级一致）
TERMINAL_STATIC = {BROKEN, EMPTY, UNKNOWN}


def empty_facts() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "rules_version": FACTS_RULES_VERSION,
        "generated_at": 0.0,
        "manifests": {},
        "items": {},
    }


def manifest_hashes(manifests: dict[str, Any]) -> dict[str, str]:
    """清单内容哈希（id → 该条目所属清单文件的 sha256），任一清单变即整份重建。"""
    out: dict[str, str] = {}
    for manifest_path in {m.path for m in manifests.values()}:
        try:
            out[manifest_path.name] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        except OSError:
            out[manifest_path.name] = ""
    return out


def compute_item(store: Any, item: Any) -> dict[str, Any] | None:
    """单个 v2 条目的烘焙事实；v1（未迁移、无真实文件）返回 None（回退惰性计算）。"""
    if not store._is_v2_item(item) or not item.path.is_file():
        return None
    key = item.json_id or str(item.path)
    try:
        raw = item.path.read_bytes()
    except OSError:
        return None
    code = store.get_code(item)
    tree = parse_code(code)
    # 本地模块判定域：文件兄弟目录 + 项目根（source_dir）。课程项目的子目录文件
    # （controllers/x.py）import 项目顶层包（application/common/config）是正常结构——
    # 只看兄弟目录会把它们误判为第三方、打出永远装不上的缺依赖徽章
    local_dirs = [item.path.parent]
    if item.source_dir:
        local_dirs.append(Path(item.source_dir))
    deps = sorted(third_party_imports(code, tree, local_dirs)) if tree is not None else []
    checker = store._checker
    try:
        report = checker.check(item.path, key, content=code, tree=tree)
        static = compute_run_status(
            code,
            example_id=item.json_id,
            local_dirs=local_dirs,
            checker=checker,
            module_index=None,
        )
        findings = [
            {"description": r.description, "category": r.category}
            for r in report.risk_details
            if r.level.name == "HIGH"
        ]
    except Exception:  # noqa: BLE001 - 单条异常降级为未知态，不让整份烘焙失败
        static, findings = UNKNOWN, []
    try:
        quality = store._scorer.score(item).score
    except Exception:  # noqa: BLE001
        quality = 0
    root = store._root_for(item.json_file) if item.json_file is not None else store.data_root
    try:
        rel = str(item.path.relative_to(root))
    except ValueError:
        rel = item.path.name
    return {
        "file": rel,
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "imports": store.import_tags(item),
        "deps": deps,
        "quality": quality,
        "risk_high": bool(findings),
        "risk_findings": findings,
        "static": static,
        "theme": store.theme_key(item),
    }


def build(store: Any, *, limit: int | None = None) -> dict[str, Any]:
    """全量烘焙（遍历索引，跳过未迁移条目）。返回可序列化的 facts 数据。"""
    data = empty_facts()
    data["manifests"] = manifest_hashes(store._manifests)
    for item in list(store.index.values()):
        if limit is not None and len(data["items"]) >= limit:
            break
        entry = compute_item(store, item)
        if entry is not None:
            data["items"][item.json_id or str(item.path)] = entry
    data["generated_at"] = time.time()
    return data


def load(path: Path) -> dict[str, Any] | None:
    """读 facts 文件；结构/版本不符按未命中处理（不抛异常）。"""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("schema_version") != SCHEMA_VERSION or raw.get("rules_version") != FACTS_RULES_VERSION:
        return None
    if not isinstance(raw.get("items"), dict) or not isinstance(raw.get("manifests"), dict):
        return None
    return raw


def adopt(data: dict[str, Any], store: Any) -> tuple[dict[str, Any], str]:
    """从烘焙数据采纳事实：逐条按「清单哈希 + 文件哈希」判定，未命中才重算。

    与 ``build`` 全量重算**结果等价**（对命中条目是同一份数据，对未命中条目当场重算），
    但稳态下省掉 ≈1.7s 的 AST/评分开销，只付 ≈20ms 的哈希成本。

    返回 ``(items, status)``：``hit`` = 全部命中；``partial`` = 有条目重算（需落缓存）。
    """
    manifests_now = manifest_hashes(store._manifests)
    stale_manifests = {
        name for name, digest in manifests_now.items() if data["manifests"].get(name) != digest
    }
    items: dict[str, Any] = {}
    recomputed = 0
    for key, item in store.index.items():
        entry = data["items"].get(key)
        manifest_name = item.json_file.name if item.json_file is not None else ""
        if isinstance(entry, dict) and manifest_name not in stale_manifests and _entry_matches(entry, item):
            items[key] = entry
            continue
        fresh = compute_item(store, item)
        if fresh is not None:
            items[key] = fresh
            recomputed += 1
    status = "hit" if recomputed == 0 and len(items) == len(store.index) else "partial"
    return items, status


def _entry_matches(entry: dict[str, Any], item: Any) -> bool:
    try:
        return hashlib.sha256(item.path.read_bytes()).hexdigest() == entry.get("sha256")
    except OSError:
        return False


def make_data(store: Any, items: dict[str, Any]) -> dict[str, Any]:
    """把采纳/重算后的事实包成可落盘的数据（头部与 ``build`` 同形）。"""
    data = empty_facts()
    data["manifests"] = manifest_hashes(store._manifests)
    data["items"] = items
    data["generated_at"] = time.time()
    return data


def fingerprint(data: dict[str, Any]) -> str:
    """整份事实的稳定指纹（日志/诊断用）。"""
    h = hashlib.sha256()
    for name, digest in sorted(data.get("manifests", {}).items()):
        h.update(f"{name}:{digest}".encode())
    for key, entry in sorted(data.get("items", {}).items()):
        h.update(f"{key}:{entry.get('sha256', '')}".encode())
    return h.hexdigest()[:16]

# ---------------------------------------------------------------------------
# 依赖清单聚合口径（requirements.txt 汇总 / 缺依赖修复共用；不是 PyPI 包的直接剔除）
# ---------------------------------------------------------------------------
# 装不上的历史名（原名自退役的 scripts/gen_shared_requirements.py）（自退役的 scripts/gen_shared_requirements.py 原样继承，勿删）：
# - pycrypto / typed-ast / pyqt5 / autotest：无 wheel 或源码编译必败，pip 报错即整份清单失败；
# - c01 / c1104 / corner-widget / tencentyoutuyun / ternary-new：原仓库源码里的无效导入名，
#   PyPI 上不存在（ternary-new 是科研绘图示例内嵌的本地模块，不是包）。
EXCLUDED_PKGS = {
    "pycrypto",
    "typed-ast",
    "pyqt5",
    "autotest",
    "c01",
    "c1104",
    "corner-widget",
    "tencentyoutuyun",
    "ternary-new",
}

def _norm_pkg(raw: str) -> str | None:
    """规范化包名（PEP 503 小写去点），非法/带版本约束的输入返回 None。"""
    name = raw.strip().split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split(">")[0].split("<")[0]
    name = name.split("[")[0].strip()
    if not VALID_PKG_RE.match(name):
        return None
    return name.lower().replace("_", "-")


def _local_module_names(root: Path) -> set[str]:
    """示例树里能被 PYTHONPATH 解析的本地模块名（示例项目自己的包，不是 PyPI 包）。

    - ``projects/movie-cat`` 这类多目录项目会 import 自己的 ``common`` / ``config``
      （未必有 ``__init__.py``，靠 __main__ 目录在 sys.path 上解析）；
    - ``examples_assets/.../ternary_new`` 是被示例源码内联引用的随仓库小库；
    把它们写进 requirements.txt 会让 pip 报"找不到包"而拖垮整份清单。
    """
    names: set[str] = set()
    for top in ("topics", "tools", "projects", "examples_assets"):
        base = root / top
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_dir():
                if any(path.glob("*.py")) or (path / "__init__.py").is_file() or any(path.rglob("*.py")):
                    names.add(path.name)
            elif path.suffix == ".py":
                names.add(path.stem)
    return names


