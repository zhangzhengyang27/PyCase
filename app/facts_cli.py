#!/usr/bin/env python3
"""构建期派生数据工具（契约 §3.2 烘焙索引 / §2.4 依赖汇总的最小替代）。

子命令：
- ``bake``          全量烘焙 ``json_examples/facts.json``（改数据后跑，随包分发）
- ``check``         校验仓库里的烘焙文件是否命中（CI 门禁：失配退出 1）
- ``requirements``  汇总仓库根 ``requirements.txt``（清单 requirements + 烘焙依赖分析）

用法：
    python -m app.facts_cli bake
    python -m app.facts_cli check
    python -m app.facts_cli requirements [--check]

说明：``requirements`` 是只读聚合（仓库根 ``scripts/gen_shared_requirements.py``
随 scripts/ 退役后的等价替代）：输入是清单里的 ``requirements`` 元数据与
烘焙索引里的逐文件 import 分析，不再重扫源码。
"""

import argparse
import sys
from pathlib import Path

from . import facts as facts_mod
from .facts import EXCLUDED_PKGS, _local_module_names, _norm_pkg
from .contract_store import ContractStore
from .importer import IMPORT_TO_PKG
from .logger import configure_logging, get_logger

ROOT = Path(__file__).resolve().parent.parent
BUILTIN_ROOT = ROOT / "json_examples"
USER_ROOT = ROOT / "user_examples"
REQUIREMENTS_OUT = ROOT / "requirements.txt"

_HEADER = """# 全项目共享依赖清单（自动生成，勿手改）：python -m app.facts_cli requirements
# 模型：本项目是一个应用，json_examples 里的示例是它的模块；
# 共享 .venv 首次创建时由 venv_manager 按本清单安装。
"""


def _store() -> ContractStore:
    store = ContractStore(
        collection_dir=BUILTIN_ROOT,
        data_root=ROOT,
        workspace_root=ROOT / ".json_examples_cache",
        user_dir=USER_ROOT,
    )
    store.load()
    return store


def collect_requirements(store: ContractStore) -> list[str]:
    """依赖汇总：清单 requirements 元数据 + 烘焙 import 分析的并集（PEP 503 规范化去重）。"""
    names: set[str] = set()

    def add(raw: str) -> None:
        pkg = _norm_pkg(raw)
        if pkg and pkg not in EXCLUDED_PKGS:
            names.add(pkg)

    for manifest in store._manifests.values():
        for entry in manifest.entries:
            for req in entry.requirements or []:
                add(str(req))
    local_modules = _local_module_names(ROOT)
    for item in store.index.values():
        facts_entry = store._fact_entry(item)
        for mod in (facts_entry or {}).get("deps") or []:
            if mod in local_modules:
                continue
            add(IMPORT_TO_PKG.get(mod, mod))
    return sorted(names)


def _cmd_bake() -> int:
    store = _store()
    dest = store.facts_shipped_path()
    data = store.bake_facts(dest)
    print(
        f"[bake] 写入 {dest}：条目 {len(data['items'])}，清单 {len(data['manifests'])}，"
        f"指纹 {facts_mod.fingerprint(data)}"
    )
    return 0


def _cmd_check() -> int:
    store = _store()
    data = facts_mod.load(store.facts_shipped_path())
    if data is None:
        print("[check] 烘焙文件缺失或版本不符", file=sys.stderr)
        return 1
    items, status = facts_mod.adopt(data, store)
    if status != "hit":
        stale = [key for key in store.index if key not in items or items[key] != data["items"].get(key)]
        print(f"[check] 烘焙文件未命中（{len(stale)} 条失配，如 {stale[:3]}）；请重跑 bake", file=sys.stderr)
        return 1
    print(f"[check] 命中：条目 {len(items)}，指纹 {facts_mod.fingerprint(data)}")
    return 0


def render_requirements(names: list[str]) -> str:
    """requirements.txt 的完整文本（生成与校验共用同一份，防两处漂移）。"""
    return _HEADER + "\n" + "\n".join(names) + "\n"


def _cmd_requirements(check_only: bool) -> int:
    store = _store()
    names = collect_requirements(store)
    body = render_requirements(names)
    if check_only:
        current = REQUIREMENTS_OUT.read_text(encoding="utf-8") if REQUIREMENTS_OUT.is_file() else ""
        if current != body:
            print("[requirements] 仓库根 requirements.txt 与聚合结果不一致；请重跑生成", file=sys.stderr)
            return 1
        print(f"[requirements] 一致：{len(names)} 个包")
        return 0
    REQUIREMENTS_OUT.write_text(body, encoding="utf-8")
    print(f"[requirements] 写入 {REQUIREMENTS_OUT}：{len(names)} 个包")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="构建期派生数据工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bake", help="全量烘焙 facts.json")
    sub.add_parser("check", help="校验 facts.json 是否命中")
    req = sub.add_parser("requirements", help="汇总 requirements.txt")
    req.add_argument("--check", action="store_true", help="只校验不写盘")
    args = ap.parse_args(argv)

    configure_logging()
    get_logger(__name__)
    if args.cmd == "bake":
        return _cmd_bake()
    if args.cmd == "check":
        return _cmd_check()
    return _cmd_requirements(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
