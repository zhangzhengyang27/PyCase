#!/usr/bin/env python3
"""示例库健康审计：排查无效/可疑示例（只读，不运行任何示例代码）。

检查维度：
  1. 结构完整性：id/name/category/code 缺失或为空、id 重复、name 非 .py 后缀
  2. 语法有效性：ast.parse 失败（无法运行、编辑器高亮失效，判「无效」的硬指标）
  3. 空壳代码：去除 docstring 后没有实际语句（或代码过短）
  4. 完全重复：code 内容相同的分组（同一份代码拷贝多个名字）
  5. 依赖缺失：第三方顶层 import 在共享 .venv 中不存在（运行必 ImportError）
  6. 安全高危：复用 app/security.py 的 AST 扫描，列 HIGH 风险项
  7. dir 有效性：dir 指向的原始目录不存在（物化会降级为裸文件，丢失兄弟模块）

用法（须用共享 .venv 解释器，依赖检查才有意义）：
  .venv/bin/python scripts/audit_examples.py [--json 出路]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 注意：把 ROOT 插入 sys.path 后，find_spec 会把仓库顶层目录（app/tools/
# projects/scripts/tests）误判为可导入模块——依赖缺失检查对这类同名模块
# 存在盲区（当前 7 个缺失名不冲突，新增检查维度时须留意）
sys.path.insert(0, str(ROOT))

from app.security import RiskLevel, SecurityChecker  # noqa: E402

JSON_DIR = ROOT / "json_examples"


def load_all() -> list[dict]:
    items = []
    for path in sorted(JSON_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for idx, it in enumerate(data.get("examples", []) if isinstance(data, dict) else data):
            items.append({"_file": path.name, "_idx": idx, **it})
    return items


def ref_of(it: dict) -> str:
    return f"{it.get('name', '?')} ({it['_file']}#{it['_idx']})"


def third_party_imports(code: str, dir_path: Path | None) -> set[str]:
    """顶层第三方 import（排除标准库与示例目录内的本地模块）。"""
    mods: set[str] = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 示例代码的无效转义 SyntaxWarning 不入耳
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return mods
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    stdlib = set(sys.stdlib_module_names)
    return {
        m
        for m in mods
        if m not in stdlib and not (dir_path and ((dir_path / f"{m}.py").exists() or (dir_path / m).is_dir()))
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="完整结果写出到该 JSON 文件")
    args = parser.parse_args()

    items = load_all()
    report: dict[str, list] = defaultdict(list)

    # 1) 结构完整性
    seen_ids: dict[str, str] = {}
    for it in items:
        ref = ref_of(it)
        for field in ("id", "name", "category", "code"):
            if not (it.get(field) or "").strip():
                report["结构缺失"].append(f"{ref} 缺 {field}")
        if it.get("name") and not str(it["name"]).endswith(".py"):
            report["结构缺失"].append(f"{ref} name 非 .py 后缀: {it['name']}")
        iid = str(it.get("id") or "")
        if iid in seen_ids:
            report["id 重复"].append(f"{ref} 与 {seen_ids[iid]} 同 id")
        else:
            seen_ids[iid] = ref

    # 2/3) 语法与空壳 + 5) 依赖收集
    third: dict[str, set[str]] = {}  # 模块名 -> 引用它的示例 ref
    for it in items:
        ref = ref_of(it)
        code = it.get("code") or ""
        if not code.strip():
            continue  # 已记入结构缺失
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                report["语法错误"].append(f"{ref} L{e.lineno}: {e.msg}")
                continue
        body = [n for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if not body or len(code.strip()) < 30:
            report["空壳代码"].append(f"{ref} ({len(code.strip())} 字符)")
        dir_path = ROOT / it["dir"] if it.get("dir") else None
        for m in third_party_imports(code, dir_path):
            third.setdefault(m, set()).add(ref)

    # 4) 完全重复（按 code 哈希分组）
    by_hash: dict[str, list[str]] = defaultdict(list)
    for it in items:
        code = it.get("code") or ""
        if len(code.strip()) >= 30:
            by_hash[hashlib.md5(code.encode()).hexdigest()].append(ref_of(it))
    for group in by_hash.values():
        if len(group) > 1:
            report["完全重复"].append(" ≡ ".join(group[:4]) + (" …" if len(group) > 4 else ""))

    # 5) 依赖缺失（在当前解释器下探查；请用 .venv/bin/python 运行本脚本）
    for mod, refs in sorted(third.items()):
        try:
            if importlib.util.find_spec(mod) is not None:
                continue
        except (ValueError, ModuleNotFoundError, ImportError):
            pass
        report["依赖缺失"].append(f"{mod} ← {len(refs)} 个示例，如 {sorted(refs)[0]}")

    # 6) 安全高危（复用应用自身的 AST 扫描与白名单）
    checker = SecurityChecker()
    for it in items:
        code = it.get("code") or ""
        if not code.strip():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue
        rep = checker.check(Path(it.get("name") or "x.py"), str(it.get("id") or ""), content=code, tree=tree)
        highs = [r.description for r in rep.risk_details if r.level == RiskLevel.HIGH]
        if highs:
            report["安全高危"].append(f"{ref_of(it)}：{'；'.join(highs[:2])}")

    # 7) dir 有效性
    for it in items:
        d = it.get("dir") or ""
        if d and not (ROOT / d).is_dir():
            report["dir 失效"].append(f"{ref_of(it)} → {d}")

    # 汇总输出
    print(f"审计范围：{len(items)} 个示例（{len(list(JSON_DIR.glob('*.json')))} 个集合文件）\n")
    order = ["结构缺失", "id 重复", "语法错误", "空壳代码", "完全重复", "依赖缺失", "安全高危", "dir 失效"]
    total_bad = 0
    flagged: set[str] = set()
    for key in order:
        rows = report.get(key, [])
        total_bad += len(rows)
        print(f"【{key}】{len(rows)} 条")
        for row in rows[:8]:
            print(f"  - {row}")
        if len(rows) > 8:
            print(f"  … 另 {len(rows) - 8} 条")
    print(f"\n结论：{total_bad} 条问题记录（去重后涉及示例见 --json）")

    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"完整清单已写出：{args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
