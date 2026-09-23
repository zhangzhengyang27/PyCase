#!/usr/bin/env python3
"""示例库修复（v0.7 审计处置）：三步全部确定性、幂等；删除项靠 git 历史回滚。

  A. 下架空壳 __init__.py：无 code，或去除 docstring 后无实际语句的包标记文件；
  B. 合并完全重复：同 code 分组，保留名字更语义化的那个（同代码 = 同质量分，
     差异只在命名）；通用名表 main/get/test/app… 判定为非语义化；
  C. dir 上调：本地兄弟模块不在物化目录时，向上找能同时解析全部缺失模块的
     最近祖先目录；找不到（真缺 pip 包/模块）则保持原样并列入未决清单。

用法：python3 scripts/fix_examples.py [--apply]
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "json_examples"
GENERIC_NAMES = {"main", "get", "set", "run", "test", "app", "demo", "code", "new", "tmp", "temp"}
MIN_CODE = 30


def parse(code: str) -> ast.Module | None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return ast.parse(code)
        except SyntaxError:
            return None


def is_shell(code: str) -> bool:
    """去除 docstring 后没有实际语句。"""
    tree = parse(code)
    if tree is None:
        return False
    body = [
        n
        for n in tree.body
        if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))
    ]
    return not body


def local_imports(code: str, dir_path: Path) -> set[str]:
    """非标准库且在 dir_path 下解析不到的顶层 import（本地兄弟模块缺失）。"""
    tree = parse(code)
    if tree is None:
        return set()
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    stdlib = set(sys.stdlib_module_names)
    missing: set[str] = set()
    for m in mods:
        if m in stdlib:
            continue
        if (dir_path / f"{m}.py").exists() or (dir_path / m).is_dir():
            continue
        # 已安装在共享 .venv 的 pip 包不算缺失（须用 .venv 解释器运行本脚本）
        try:
            if importlib.util.find_spec(m) is not None:
                continue
        except (ValueError, ModuleNotFoundError, ImportError):
            pass
        missing.add(m)
    return missing


def main() -> int:
    apply = "--apply" in sys.argv
    collections: dict[Path, dict] = {}
    for path in sorted(JSON_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "examples" in data:
            collections[path] = data

    all_items = [(p, it) for p, d in collections.items() for it in d["examples"]]

    # ---- A. 下架空壳 __init__.py ----
    shell_ids: set[int] = set()
    for p, it in all_items:
        if it.get("name") != "__init__.py":
            continue
        code = it.get("code") or ""
        if not code.strip() or is_shell(code):
            shell_ids.add(id(it))  # 直接按对象标记：同名 __init__ 不得互相牵连
    removed_shells = [f"{it['name']} ({p.name})" for p, it in all_items if id(it) in shell_ids]
    alive = [(p, it) for p, it in all_items if id(it) not in shell_ids]

    # ---- B. 合并完全重复（同代码 = 同质量分，保留语义化命名者）----
    removed_dups: list[str] = []
    by_hash: dict[str, list[tuple[Path, dict]]] = {}
    for p, it in alive:
        code = it.get("code") or ""
        if len(code.strip()) >= MIN_CODE:
            by_hash.setdefault(hashlib.md5(code.encode()).hexdigest(), []).append((p, it))
    dup_remove_ids: set[int] = set()
    for group in by_hash.values():
        if len(group) <= 1:
            continue
        ranked = sorted(
            group,
            key=lambda pi: (pi[1].get("name", "").lower() in GENERIC_NAMES, pi[1].get("name", "").lower()),
        )
        for p, it in ranked[1:]:
            dup_remove_ids.add(id(it))
            removed_dups.append(f"{it['name']} ({p.name}) ≡ 保留 {ranked[0][1]['name']}")
    alive = [(p, it) for p, it in alive if id(it) not in dup_remove_ids]

    # ---- C. dir 上调 ----
    hoisted: list[str] = []
    unresolved: list[str] = []
    for p, it in alive:
        dir_rel = it.get("dir") or ""
        code = it.get("code") or ""
        if not dir_rel or not code.strip():
            continue
        dpath = ROOT / dir_rel
        if not dpath.is_dir():
            continue
        missing = local_imports(code, dpath)
        if not missing:
            continue
        cur = dpath
        resolved: Path | None = None
        while cur != ROOT and cur != cur.parent:
            cur = cur.parent
            if all((cur / f"{m}.py").exists() or (cur / m).is_dir() for m in missing):
                resolved = cur
                break
        if resolved and resolved != dpath and ROOT in resolved.parents:
            new_rel = resolved.relative_to(ROOT).as_posix()
            it["dir"] = new_rel
            hoisted.append(f"{it['name']}: {dir_rel} → {new_rel}")
        else:
            unresolved.append(f"{it['name']} 缺 {sorted(missing)}（真缺，需装包或补文件）")

    print(f"A. 下架空壳 __init__.py：{len(removed_shells)}")
    print(f"B. 合并完全重复：{len(removed_dups)}")
    for row in removed_dups[:10]:
        print(f"   - {row}")
    if len(removed_dups) > 10:
        print(f"   … 另 {len(removed_dups) - 10} 组")
    print(f"C. dir 上调：{len(hoisted)}")
    for row in hoisted[:10]:
        print(f"   - {row}")
    if len(hoisted) > 10:
        print(f"   … 另 {len(hoisted) - 10} 个")
    print(f"   未决（真缺依赖，保持原样）：{len(unresolved)}")
    for row in unresolved[:8]:
        print(f"   - {row}")

    if apply:
        for p, data in collections.items():
            before = len(data["examples"])
            data["examples"] = [
                it
                for it in data["examples"]
                if id(it) not in shell_ids and id(it) not in dup_remove_ids
            ]
            if len(data["examples"]) != before:
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"写回 {p.name}: {before} → {len(data['examples'])}")
        print("已写回（git checkout 可整体回滚）")
    else:
        print("（dry-run，未写回；加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
