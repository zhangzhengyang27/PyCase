"""契约 v1 → v2 迁移 CLI（薄入口，实现体在 ``app/migration.py``）。

用法（在仓库根执行）：

    python -m app.migration_cli --dry-run          # 输出逐集合变更计划与校验报告，不落盘
    python -m app.migration_cli --apply            # 备份 + 原子写；报告非空即拒写
    python -m app.migration_cli --verify           # 迁移后逐条语义等价断言
    python -m app.migration_cli --rollback <ts>    # 按备份还原（并删除迁移新建的源码文件）

纪律：``--apply`` 前必须先在**完整副本**上跑通 dry-run → apply → verify → rollback
（G8 护栏固化该演练）；通过前不得把 v2 清单/源码树用于任何发布。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .migration import MigrationPlan, apply_plan, backup_root_of, build_plan, rollback, verify_migration

ROOT = Path(__file__).resolve().parent.parent
BUILTIN_ROOT = ROOT / "json_examples"
DATA_ROOT = ROOT
USER_ROOT = (
    Path.home()
    / "Library"
    / "Application Support"
    / "python-example-manager-electron"
    / "user_examples"
)


def _report(plan: MigrationPlan) -> None:
    s = plan.summary()
    print(json.dumps(s, ensure_ascii=False, indent=1))
    for issue in plan.issues:
        print(f"  [{issue.level}] {issue.code} {issue.where}: {issue.message}")


def _snapshot(plan: MigrationPlan) -> dict[Path, dict]:
    return {
        m.path: json.loads(m.path.read_text(encoding="utf-8")) for m in plan.manifests
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="数据契约 v1 → v2 迁移")
    ap.add_argument("--dry-run", action="store_true", help="只输出计划，不落盘")
    ap.add_argument("--apply", action="store_true", help="执行迁移（先备份）")
    ap.add_argument("--verify", action="store_true", help="迁移后逐条等价断言")
    ap.add_argument("--rollback", metavar="TS", help="按备份时间戳还原")
    ap.add_argument("--builtin-root", default=str(BUILTIN_ROOT))
    ap.add_argument("--data-root", default=str(DATA_ROOT))
    ap.add_argument("--user-root", default=str(USER_ROOT))
    args = ap.parse_args(argv)

    builtin = Path(args.builtin_root)
    data_root = Path(args.data_root)
    user_root = Path(args.user_root)
    plan = build_plan(builtin, data_root, user_root)

    if args.dry_run:
        _report(plan)
        print("[dry-run] 未落盘")
        return 1 if plan.errors else 0

    if args.apply:
        if plan.errors:
            _report(plan)
            print("[apply] 校验发现错误，拒绝执行（报告非空即拒写）", file=sys.stderr)
            return 1
        snapshot = _snapshot(plan)
        ts, backup_dirs = apply_plan(plan, backup_root_of)
        issues = verify_migration(
            [m.path for m in plan.manifests], snapshot, plan.renamed_ids
        )
        for issue in issues:
            print(
                f"  [{issue.level}] {issue.code} {issue.where}: {issue.message}",
                file=sys.stderr,
            )
        if issues:
            print(f"[apply] 复验未通过，请回滚：--rollback {ts}", file=sys.stderr)
            return 1
        print(f"[apply] 完成并通过逐条复验；备份 {ts} 在 {len(backup_dirs)} 处")
        return 0

    if args.verify:
        # 独立复验：以最近一次备份里的 v1 快照为基线，断言**当前**清单与源码逐条等价
        backups = sorted((builtin / ".backup").glob("*"))
        if not backups:
            print("[verify] 找不到备份目录，无法复验", file=sys.stderr)
            return 1
        latest = backups[-1]
        snapshot: dict[Path, dict] = {}
        # 备份目录里除清单副本外还有回滚记录（*.rollback.json）：按记录取真实清单路径，
        # 避免把记录本身当清单解析，也避免用未解析路径去比对
        for record_path in sorted(latest.glob("*.rollback.json")):
            record = json.loads(record_path.read_text(encoding="utf-8"))
            manifest_path = Path(record["manifest"])
            backup = latest / manifest_path.name
            snapshot[manifest_path] = json.loads(backup.read_text(encoding="utf-8"))
        issues = verify_migration(sorted(snapshot.keys()), snapshot, plan.renamed_ids)
        for issue in issues:
            print(
                f"  [{issue.level}] {issue.code} {issue.where}: {issue.message}",
                file=sys.stderr,
            )
        print("[verify] " + ("通过" if not issues else f"{len(issues)} 项不一致"))
        return 1 if issues else 0

    if args.rollback:
        candidates = [
            builtin / ".backup" / args.rollback,
            user_root / ".backup" / args.rollback,
        ]
        dirs = [d for d in candidates if d.is_dir()]
        if not dirs:
            print(f"[rollback] 备份不存在: {args.rollback}", file=sys.stderr)
            return 1
        touched = rollback(dirs)
        print(f"[rollback] 已还原/删除 {len(touched)} 个路径（{len(dirs)} 处备份）")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
