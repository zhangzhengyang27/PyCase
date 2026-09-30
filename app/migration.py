"""数据契约 v1 → v2 迁移（契约 §6）。

四步：``plan``（dry-run，不落盘）→ ``apply``（先备份后原子写）→ ``verify``（逐条语义等价）
→ ``rollback``（按备份还原并删除迁移新建的源码文件）。

纪律（契约 §6.2）：
- **报告非空即拒写**——校验发现 error 时 apply 直接拒绝；
- apply 只做清单里列出的变更，不触示例内容语义（空白与注释都不改）；
- verify 要求条数、id 集合、``code`` ↔ 真实文件**逐字节**、各元数据字段逐一相等；
- 通过前不得把 v2 清单/源码树用于任何发布。

本模块同时是**运行库**（sidecar 自动迁移用户集合时复用）与 CLI 的实现体
（CLI 入口见 ``app/migration_cli.py``，不写进冻结的 ``scripts/``）。
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from .logger import get_logger
from .manifest_v2 import SCHEMA_VERSION, load_manifest

# 迁移只改这些字段，其余原样保留（未知字段不丢弃）
_META_KEYS = ("id", "name", "title", "category", "tags", "description", "requirements")


@dataclass
class FileWrite:
    """一条待写（或待确认已在位）的源码文件。"""

    path: Path
    content: str
    action: str  # 'create' | 'verify-in-place'
    entry_id: str
    collection: str


@dataclass
class ManifestRewrite:
    """一份待改写的清单：新对象 + 结构说明（供 apply/rollback 使用）。"""

    path: Path
    new_data: dict[str, Any]
    writes: list[FileWrite] = field(default_factory=list)


@dataclass
class PlanIssue:
    level: str  # 'error' | 'warning'
    code: str
    where: str
    message: str


@dataclass
class MigrationPlan:
    manifests: list[ManifestRewrite] = field(default_factory=list)
    issues: list[PlanIssue] = field(default_factory=list)
    # 改名按 (清单文件名, 旧 id) → 新 id：同名 id 在不同集合里的命运不同
    renamed_ids: dict[str, str] = field(default_factory=dict)
    # 迁移会新建的文件（回滚时删除；原位文件不在其中）
    created_files: list[Path] = field(default_factory=list)

    @property
    def errors(self) -> list[PlanIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def total_entries(self) -> int:
        return sum(len(m.new_data.get("examples", [])) for m in self.manifests)

    def summary(self) -> dict[str, Any]:
        by_action: dict[str, int] = {}
        for m in self.manifests:
            for w in m.writes:
                by_action[w.action] = by_action.get(w.action, 0) + 1
        return {
            "collections": len(self.manifests),
            "entries": self.total_entries,
            "writes": by_action,
            "renamed_ids": len(self.renamed_ids),
            "errors": len(self.errors),
            "warnings": len([i for i in self.issues if i.level == "warning"]),
        }


def _iter_manifests(roots: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root and Path(root).is_dir():
            out.extend(sorted(Path(root).glob("*.json")))
    return out


def build_plan(
    builtin_root: Path, data_root: Path, user_root: Path | None = None
) -> MigrationPlan:
    """扫描内置 + 用户集合，产出逐文件变更计划；不落盘。"""
    plan = MigrationPlan()
    taken_ids: set[str] = set()

    for manifest_path in _iter_manifests(
        [builtin_root, user_root] if user_root else [builtin_root]
    ):
        m = load_manifest(manifest_path)
        # 校验报告全量上报（警告也进 plan.issues，让 dry-run 输出完整）：
        # 阻断落盘的只有 error（CLI 的"报告非空即拒写"= errors 非空）；
        # 警告是数据质量提示（如 id 字符集 22 条），不阻塞迁移。
        for level, issues in (("error", m.report.errors), ("warning", m.report.warnings)):
            for issue in issues:
                plan.issues.append(
                    PlanIssue(level, issue.code, f"{manifest_path.name}:{issue.entry}", issue.message)
                )

        if not m.is_v1:
            continue  # 已是 v2：不重复迁移

        stem = manifest_path.stem
        manifest_dir = manifest_path.parent.resolve()
        new_entries: list[dict[str, Any]] = []
        rewrite = ManifestRewrite(path=manifest_path, new_data={}, writes=[])

        for entry in m.entries:
            # id 冲突：内置 id 永不改；用户集合冲突项加 _2 后缀（契约 §6.1）
            entry_id = entry.id
            if entry_id in taken_ids:
                backup_id = entry_id
                n = 2
                while f"{backup_id}_{n}" in taken_ids:
                    n += 1
                entry_id = f"{backup_id}_{n}"
                plan.renamed_ids[f"{manifest_path.name}:{backup_id}"] = entry_id
                plan.issues.append(
                    PlanIssue(
                        "warning",
                        "id-renamed",
                        f"{manifest_path.name}:{backup_id}",
                        f"id 冲突，改名为 {entry_id}",
                    )
                )
            taken_ids.add(entry_id)

            # 基底取原条目（未知字段保留），再覆盖迁移涉及的字段
            raw_entry: dict[str, Any] = next(
                (e for e in m.raw.get("examples", []) if str(e.get("id")) == entry.id),
                {},
            )
            new_entry: dict[str, Any] = dict(raw_entry)
            new_entry["id"] = entry_id
            for key in _META_KEYS:
                if key != "id":
                    new_entry[key] = getattr(entry, key)
            new_entry.pop("code", None)
            new_entry.pop("dir", None)

            code = entry.code if isinstance(entry.code, str) else None
            if entry.source_dir:
                # 目录型：源码归位（原位保留出处），不做搬家
                target = (data_root / entry.source_dir / entry.name).resolve()
                if not target.is_relative_to(Path(data_root).resolve()):
                    plan.issues.append(
                        PlanIssue(
                            "error",
                            "dir-outside-root",
                            f"{manifest_path.name}:{entry_id}",
                            f"dir 越界: {entry.source_dir}",
                        )
                    )
                    continue
                rel = os.path.relpath(target, manifest_dir).replace(os.sep, "/")
                new_entry["file"] = rel
                if code is None:
                    plan.issues.append(
                        PlanIssue(
                            "error",
                            "code-missing",
                            f"{manifest_path.name}:{entry_id}",
                            "v1 条目既无 code 也无目录，无法迁移",
                        )
                    )
                    continue
                if target.exists():
                    existing = target.read_text(
                        encoding="utf-8", errors="surrogateescape"
                    )
                    if existing != code:
                        # 契约只允许「逐字节一致」与「缺失」两态：内容不一致必须暴露，不能静默覆盖
                        plan.issues.append(
                            PlanIssue(
                                "error",
                                "dir-content-conflict",
                                f"{manifest_path.name}:{entry_id}",
                                f"原位文件与清单 code 不一致（{target}）：需人工确认后再迁移",
                            )
                        )
                        continue
                    action = "verify-in-place"
                else:
                    action = "create"
                    plan.created_files.append(target)
                rewrite.writes.append(
                    FileWrite(target, code, action, entry_id, manifest_path.name)
                )
            else:
                # 单文件：外移到 <集合根>/<stem>/<name>
                target = (manifest_dir / stem / entry.name).resolve()
                rel = os.path.relpath(target, manifest_dir).replace(os.sep, "/")
                new_entry["file"] = rel
                if code is None:
                    plan.issues.append(
                        PlanIssue(
                            "error",
                            "code-missing",
                            f"{manifest_path.name}:{entry_id}",
                            "v1 条目缺少 code，无法外移",
                        )
                    )
                    continue
                plan.created_files.append(target)
                rewrite.writes.append(
                    FileWrite(target, code, "create", entry_id, manifest_path.name)
                )

            new_entries.append(new_entry)

        # 顶层：保留 v1 的自定义键，覆盖 schema_version 与 examples
        new_data: dict[str, Any] = dict(m.raw)
        new_data["schema_version"] = SCHEMA_VERSION
        new_data["name"] = m.name
        new_data["description"] = m.description
        new_data["examples"] = new_entries
        rewrite.new_data = new_data
        plan.manifests.append(rewrite)

    return plan


def _atomic_write(path: Path, text: str) -> None:
    """原子写：同目录 tmp + os.replace（写失败不损坏原文件、无 .tmp 残留）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def apply_plan(
    plan: MigrationPlan, backup_root_of: Callable[[Path], Path]
) -> tuple[str, list[Path]]:
    """执行迁移：先备份清单与**原位文件**，再原子写；返回 ``(时间戳, 备份目录列表)``。

    每个集合的备份目录（契约：集合根下 ``.backup/<ts>/``）内容：
    - ``<清单名>.json``：v1 清单副本；
    - ``files/<n>__<名>``：原位文件副本（**编号前缀**避免同名文件互相覆盖）；
    - ``<清单名>.rollback.json``：本次**新建**的文件路径（回滚时删）与原位文件的还原目标。

    先落源码文件、再改清单：任何一步失败都不会让清单指向不存在的文件。
    """
    if plan.errors:
        raise RuntimeError(
            f"迁移计划存在 {len(plan.errors)} 个错误，拒绝执行（报告非空即拒写）"
        )
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup_dirs: list[Path] = []

    for rewrite in plan.manifests:
        backup_dir = backup_root_of(rewrite.path) / ts
        files_dir = backup_dir / "files"
        backup_dir.mkdir(parents=True, exist_ok=True)
        if backup_dir not in backup_dirs:
            backup_dirs.append(backup_dir)

        shutil.copy2(rewrite.path, backup_dir / rewrite.path.name)
        created: list[str] = []
        inplace: list[dict[str, str]] = []
        for i, write in enumerate(rewrite.writes):
            if write.action == "create":
                created.append(str(write.path))
                continue
            if write.path.exists():
                files_dir.mkdir(parents=True, exist_ok=True)
                backup_name = f"{i}__{write.path.name}"
                shutil.copy2(write.path, files_dir / backup_name)
                inplace.append({"target": str(write.path), "backup": backup_name})
        (backup_dir / f"{rewrite.path.name}.rollback.json").write_text(
            json.dumps(
                {"manifest": str(rewrite.path), "created": created, "inplace": inplace},
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )

        for write in rewrite.writes:
            if write.action == "create":
                _atomic_write(write.path, write.content)
        _atomic_write(
            rewrite.path,
            json.dumps(rewrite.new_data, ensure_ascii=False, indent=1) + "\n",
        )

    if not backup_dirs:
        raise RuntimeError("计划为空，无可执行内容")
    return ts, backup_dirs


def verify_migration(
    manifest_paths: Iterable[Path],
    snapshot: dict[Path, dict[str, Any]],
    renamed_ids: dict[str, str] | None = None,
) -> list[PlanIssue]:
    """逐条语义等价断言：条数 / id 集合 / code↔file 逐字节 / 元数据字段逐一相等。

    ``snapshot`` = 迁移前的 v1 清单内容（apply 前抓取，或从备份目录读取）；
    ``manifest_paths`` 指向**当前**（迁移后）的清单文件。
    """
    issues: list[PlanIssue] = []
    renamed = renamed_ids or {}
    for path in manifest_paths:
        before = snapshot.get(path)
        if before is None:
            issues.append(
                PlanIssue(
                    "error", "verify-no-baseline", path.name, "缺少迁移前的清单快照"
                )
            )
            continue
        after = json.loads(path.read_text(encoding="utf-8"))
        old_entries = {str(e.get("id")): e for e in before.get("examples", [])}
        new_entries = {str(e.get("id")): e for e in after.get("examples", [])}

        for old_id, old in old_entries.items():
            new_id = renamed.get(f"{path.name}:{old_id}", old_id)
            new = new_entries.get(new_id)
            if new is None:
                issues.append(
                    PlanIssue(
                        "error",
                        "verify-missing",
                        f"{path.name}:{old_id}",
                        "迁移后条目缺失",
                    )
                )
                continue
            for key in (
                "name",
                "title",
                "category",
                "tags",
                "description",
                "requirements",
            ):
                if key not in old:
                    # v1 未声明的字段：迁移引入默认值属于"补齐"（与顶层 name 补齐同类），
                    # 旧数据本就没有的事实不存在漂移；已声明的字段仍必须逐字保持
                    continue
                # 归一后比较：v1 里缺失字段（None）与 v2 的空列表/空串是同一事实
                default = [] if key in ("tags", "requirements") else ""
                if (old.get(key) if old.get(key) is not None else default) != (
                    new.get(key) if new.get(key) is not None else default
                ):
                    issues.append(
                        PlanIssue(
                            "error",
                            "verify-meta-drift",
                            f"{path.name}:{old_id}",
                            f"字段 {key} 变化: {old.get(key)!r} → {new.get(key)!r}",
                        )
                    )
            code = old.get("code")
            if code is None:
                continue
            target = (path.parent.resolve() / str(new.get("file"))).resolve()
            if not target.exists():
                issues.append(
                    PlanIssue(
                        "error",
                        "verify-file-missing",
                        f"{path.name}:{old_id}",
                        f"文件不存在: {target}",
                    )
                )
                continue
            if target.read_bytes() != code.encode("utf-8"):
                issues.append(
                    PlanIssue(
                        "error",
                        "verify-bytes",
                        f"{path.name}:{old_id}",
                        f"内容与 v1 code 不一致: {target}",
                    )
                )

        # 条数：允许因 id 改名以外的差异必须暴露
        if len(new_entries) != len(old_entries):
            issues.append(
                PlanIssue(
                    "error",
                    "verify-count",
                    path.name,
                    f"条数变化: {len(old_entries)} → {len(new_entries)}",
                )
            )
    return issues


def rollback(backup_dirs: Iterable[Path]) -> list[Path]:
    """按备份还原到 v1：清单与原位文件回位、迁移新建的源码文件删除（契约 §6.2）。

    只依赖备份目录自身的内容（清单副本 + files/ + *.rollback.json），
    因此迁移后（清单已是 v2）也能正确回滚。
    """
    touched: list[Path] = []
    for backup_dir in backup_dirs:
        collection_root = backup_dir.parent.parent
        for record_path in sorted(backup_dir.glob("*.rollback.json")):
            record = json.loads(record_path.read_text(encoding="utf-8"))
            manifest_backup = backup_dir / Path(record["manifest"]).name
            if manifest_backup.exists():
                target = collection_root / manifest_backup.name
                shutil.copy2(manifest_backup, target)
                touched.append(target)
            for item in record.get("inplace", []):
                src = backup_dir / "files" / item["backup"]
                if src.exists():
                    dest = Path(item["target"])
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    touched.append(dest)
            for created in record.get("created", []):
                path = Path(created)
                if path.exists():
                    path.unlink()
                    touched.append(path)
                # 迁移为外移文件新建的目录也要清掉（rmdir 只删空目录，非空自动失败）
                _prune_empty_parents(path, collection_root)
        # 已应用的迁移不再需要该备份：清理掉，避免下次演练读到旧记录
        shutil.rmtree(backup_dir, ignore_errors=True)
    return touched


def _prune_empty_parents(path: Path, stop: Path) -> None:
    """向上清理迁移新建的空目录，直到集合根为止（只 rmdir 空目录，绝不递归删）。"""
    stop = Path(stop).resolve()
    for parent in Path(path).parents:
        if parent == stop or not parent.is_relative_to(stop):
            return
        try:
            parent.rmdir()
        except OSError:
            return  # 非空或已被别的流程清理：停手


def backup_root_of(manifest: Path) -> Path:
    """备份位置：集合根下 ``.backup/``（契约 §6.2，已 gitignore）。"""
    return manifest.parent / ".backup"


def migrate_user_collections(user_dir: Path, data_root: Path) -> str | None:
    """运行时自动迁移旧用户集合（契约 §2.4）：dry-run → apply → 复验，含备份。

    内置集合的迁移是显式动作（CLI + 演练）；用户集合在用户机器上无从手动执行，
    故在应用启动时自动完成一次，全程有备份可回滚。任何错误都不阻塞启动：
    迁移失败的用户集合保持 v1 只读可用（fail-visible，下一次启动再试）。
    返回备份时间戳（未迁移返回 None）。
    """
    user_dir = Path(user_dir)
    if not user_dir.is_dir():
        return None
    log = get_logger(__name__)
    plan = build_plan(user_dir, data_root, None)
    if not plan.manifests:
        return None
    if plan.errors:
        log.error("用户集合迁移校验未通过，本次跳过（保持 v1 只读）: %s", [i.message for i in plan.errors[:3]])
        return None
    snapshot = {m.path: json.loads(m.path.read_text(encoding="utf-8")) for m in plan.manifests}
    ts, backup_dirs = apply_plan(plan, backup_root_of)
    issues = verify_migration([m.path for m in plan.manifests], snapshot, plan.renamed_ids)
    if issues:
        log.error("用户集合迁移复验未通过，已回滚: %s", [f"{i.code}: {i.message}" for i in issues[:3]])
        rollback(backup_dirs)
        return None
    log.info("用户集合已自动迁移到契约 v2：%d 个集合，备份 %s", len(plan.manifests), ts)
    return ts
