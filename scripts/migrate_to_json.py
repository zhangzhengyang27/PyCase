#!/usr/bin/env python3
"""把现有目录中的 Python 示例批量迁移为 JSON 示例集（编排薄壳）。

核心逻辑（IMPORT_TO_PKG 映射、import 分析、标签/依赖猜测、id 去重）已收敛到
``app/importer.py``（sidecar 导入向导共用同一实现，防止两处分叉）；本脚本只保留
CLI 编排：topics/tools/projects 三分类遍历、``dir`` 字段生成（迁移示例可整体
物化兄弟模块）、pip dry-run 校验、dry-run 预览。

默认扫描向上找到的仓库根（包含 topics/tools/projects）下的示例，
生成 ``desktop-app/json_examples/migrated.json``。**原 .py 文件保留不删**。

用法：
    python scripts/migrate_to_json.py                 # 自动查找并迁移
    python scripts/migrate_to_json.py --source /path/to/repo --dry-run
    python scripts/migrate_to_json.py --output my_examples.json

生成的 JSON 可直接被应用加载（见 docs/json-examples.md）。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.importer import (  # noqa: E402
    SKIP_DIRS,
    build_source_modules,
    describe_from_readme,
    derive_tags,
    ensure_unique_id,
    extract_imports,
    guess_requirements,
    read_requirements,
    slugify,
)

SCAN_DIRS = ("topics", "tools", "projects")


def find_repo_root(start: Path) -> Path | None:
    """向上查找包含 topics/tools/projects 的目录。"""
    current = start.resolve()
    for _ in range(8):
        if all((current / d).is_dir() for d in SCAN_DIRS):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def validate_pkgs(pkgs: list[str], python_exe: str) -> set[str]:
    """用 ``pip install --dry-run`` 校验包名是否在 PyPI 存在，返回合法包名集合。"""
    valid: set[str] = set()
    for pkg in sorted(set(pkgs)):
        try:
            r = subprocess.run(
                [python_exe, "-m", "pip", "install", "--dry-run", "-q", pkg],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if r.returncode == 0:
            valid.add(pkg)
    return valid


def migrate(source: Path, output: Path, dry_run: bool, validate: bool = False) -> int:
    examples: list[dict] = []
    seen_ids: set[str] = set()
    repo_modules = build_source_modules(source)
    all_guessed: set[str] = set()

    for category in SCAN_DIRS:
        cat_dir = source / category
        if not cat_dir.is_dir():
            continue
        for py_file in sorted(cat_dir.rglob("*.py")):
            if any(part in SKIP_DIRS for part in py_file.parts):
                continue
            try:
                code = py_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel = py_file.relative_to(source).as_posix()
            # 相对源根的目录（用于运行时整体物化兄弟模块/数据文件）——迁移专属，
            # 应用内导入（app/importer.py）不生成 dir，走单文件物化
            dir_rel = "/".join(rel.split("/")[:-1])
            example_id = ensure_unique_id(slugify(rel), seen_ids)

            imports = extract_imports(code)
            declared = read_requirements(py_file.parent)
            guessed = guess_requirements(code, repo_modules)
            all_guessed.update(guessed)

            examples.append(
                {
                    "id": example_id,
                    "name": py_file.name,
                    "category": category,
                    "dir": dir_rel,
                    "tags": derive_tags(rel.split("/"), imports),
                    "description": describe_from_readme(py_file),
                    "requirements": declared,
                    "_guessed": guessed,
                    "code": code,
                }
            )

    payload = {
        "name": "迁移示例集",
        "description": "由迁移脚本从目录中的真实 .py 文件生成（原文件保留）。",
        "examples": examples,
    }

    # 合并声明依赖与猜测依赖（猜测部分可选经 pip dry-run 校验）
    if validate:
        valid = validate_pkgs(list(all_guessed), sys.executable)
        dropped = sorted(set(all_guessed) - valid)
        if dropped:
            print(f"[validate] 跳过 {len(dropped)} 个无法在 PyPI 解析的猜测包: {dropped}")
    else:
        valid = None
    for ex in examples:
        guessed = ex.pop("_guessed", [])
        if valid is not None:
            guessed = [g for g in guessed if g in valid]
        merged = list(dict.fromkeys(list(ex["requirements"]) + guessed))
        ex["requirements"] = merged

    if dry_run:
        print(f"[dry-run] 将生成 {len(examples)} 个示例 -> {output}")
        for ex in examples[:10]:
            print(f"  - {ex['id']} ({ex['category']}) tags={ex['tags']}")
        if len(examples) > 10:
            print(f"  ... 共 {len(examples)} 个")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已迁移 {len(examples)} 个示例 -> {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="把目录中的 .py 示例迁移为 JSON 示例集")
    parser.add_argument("--source", type=Path, default=None, help="示例仓库根（含 topics/tools/projects）")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "json_examples" / "migrated.json",
        help="输出 JSON 路径",
    )
    parser.add_argument("--dry-run", action="store_true", help="只预览不写文件")
    parser.add_argument(
        "--validate-reqs",
        action="store_true",
        help="用 pip install --dry-run 校验猜测出的第三方包名，丢弃 PyPI 上不存在的",
    )
    args = parser.parse_args()

    source = args.source
    if source is None:
        root = find_repo_root(ROOT)
        if root is None:
            print("未找到包含 topics/tools/projects 的仓库根，请用 --source 指定。", file=sys.stderr)
            return 1
        source = root

    return migrate(source, args.output, args.dry_run, validate=args.validate_reqs)


if __name__ == "__main__":
    raise SystemExit(main())
