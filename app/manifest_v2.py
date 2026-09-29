"""数据契约 v2：清单（只存元数据）+ 真实源码树。

契约与对稿记录见 docs/redesign-data-contract.md：
- 清单条目用 ``file`` 指向真实 .py（相对清单所在目录）；``code`` 内联与 ``dir`` 退役；
- load 期校验产出**机器可读报告**：fail-visible 而非 fail-crash（§2.3）；
- v1 清单（无 ``schema_version``、含内联 ``code``）只读兼容一个版本周期（§2.4）。

本模块只做「读 + 校验 + 路径解析」，不落盘、不碰缓存——落盘入口是运行工作区（见 sidecar）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = 2

# id 字符集：不干净不判错（改名=破坏身份，收藏/历史都按 id），只记警告
_ID_OK = re.compile(r"^[A-Za-z0-9._-]+$")
# 包名（含 extras 与版本约束前的裸名）：与 pip 的宽松口径一致，只过滤明显非法项
_PKG_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

IssueLevel = Literal["error", "warning"]


@dataclass
class ValidationIssue:
    """一条校验发现：level=error 的条目会被拒收，warning 只记录。"""

    level: IssueLevel
    code: str
    entry: str
    message: str


@dataclass
class ValidationReport:
    """一份清单的校验报告（迁移工具在严格模式下"报告非空即拒写"）。"""

    collection: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "collection": self.collection,
            "errors": [i.__dict__ for i in self.errors],
            "warnings": [i.__dict__ for i in self.warnings],
        }


@dataclass
class ManifestEntry:
    """清单条目。v2 用 file；v1 兼容期保留 code/source_dir（只读）。"""

    id: str
    name: str
    title: str = ""
    category: str = "topics"
    tags: list[str] = field(default_factory=list)
    description: str = ""
    requirements: list[str] = field(default_factory=list)
    file: str | None = None
    # v1 只读兼容：内联代码与原始仓库相对目录（v2 下为 None）
    code: str | None = None
    source_dir: str | None = None
    # 未知字段原样保留（契约：未知字段不丢弃）
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Manifest:
    """一份集合清单 + 其校验报告。``entries`` 只含通过校验的条目。"""

    path: Path
    schema_version: int
    name: str
    description: str
    entries: list[ManifestEntry]
    report: ValidationReport
    # 原始 JSON（迁移工具改写清单时用作基底：未知字段与顶层自定义键都不能丢）
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_v1(self) -> bool:
        return self.schema_version < SCHEMA_VERSION


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if isinstance(v, (str, int, float))]


def _clean_name(raw: Any) -> tuple[str, bool]:
    """name 规范化：非空、无路径分隔符、.py 结尾。返回 (名字, 是否合法)。"""
    name = str(raw or "").strip()
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        return name, False
    return name, True


def _clean_requirements(raw: Any, entry_id: str, report: ValidationReport) -> list[str]:
    pkgs: list[str] = []
    for item in _as_str_list(raw):
        bare = item.split(";")[0].split("==")[0].split(">=")[0].split("[")[0].strip()
        if bare and _PKG_OK.match(bare):
            pkgs.append(item)
        else:
            report.issues.append(
                ValidationIssue(
                    "warning",
                    "requirements-invalid",
                    entry_id,
                    f"丢弃非法依赖项: {item!r}",
                )
            )
    return pkgs


def _build_entry(
    spec: dict[str, Any], index: int, report: ValidationReport, seen_ids: set[str]
) -> ManifestEntry | None:
    entry_id = str(spec.get("id") or "").strip()
    if not entry_id:
        report.issues.append(
            ValidationIssue("error", "id-missing", f"#{index}", "缺少 id，条目被拒收")
        )
        return None
    if entry_id in seen_ids:
        report.issues.append(
            ValidationIssue(
                "warning",
                "id-duplicate",
                entry_id,
                "集合内 id 重复：保留首条，本条被拒收",
            )
        )
        return None
    seen_ids.add(entry_id)
    if not _ID_OK.match(entry_id):
        report.issues.append(
            ValidationIssue(
                "warning",
                "id-charset",
                entry_id,
                "id 含非 [A-Za-z0-9._-] 字符（保留，改名会破坏身份）",
            )
        )

    name, name_ok = _clean_name(spec.get("name"))
    if not name_ok:
        report.issues.append(
            ValidationIssue("error", "name-invalid", entry_id, f"name 非法: {name!r}")
        )
        return None

    file_field = spec.get("file")
    file_str = (
        str(file_field).strip()
        if isinstance(file_field, str) and file_field.strip()
        else None
    )

    known = {
        "id",
        "name",
        "title",
        "category",
        "tags",
        "description",
        "requirements",
        "file",
        "code",
        "dir",
    }
    extra = {k: v for k, v in spec.items() if k not in known}

    return ManifestEntry(
        id=entry_id,
        name=name,
        title=str(spec.get("title") or ""),
        category=str(spec.get("category") or "topics"),
        tags=_as_str_list(spec.get("tags")),
        description=str(spec.get("description") or ""),
        requirements=_clean_requirements(spec.get("requirements"), entry_id, report),
        file=file_str,
        code=spec.get("code") if isinstance(spec.get("code"), str) else None,
        source_dir=str(spec.get("dir")) if spec.get("dir") else None,
        extra=extra,
    )


def load_manifest(path: Path) -> Manifest:
    """读取并校验一份清单。校验失败只影响对应条目，不抛异常（fail-visible）。"""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"清单顶层必须是对象: {path}")

    collection = str(raw.get("name") or Path(path).stem)
    report = ValidationReport(collection=collection)

    version = raw.get("schema_version")
    schema_version = int(version) if isinstance(version, (int, float)) else 1
    if not isinstance(version, (int, float)):
        report.issues.append(
            ValidationIssue(
                "warning",
                "v1-legacy",
                collection,
                "缺少 schema_version：按 v1 只读兼容",
            )
        )
    elif schema_version > SCHEMA_VERSION:
        report.issues.append(
            ValidationIssue(
                "warning",
                "schema-newer",
                collection,
                f"schema_version={schema_version} 高于本程序支持",
            )
        )

    if not raw.get("name"):
        # v2 要求顶层 name 必填；缺失回退 stem 并记警告（load 期不报错）
        report.issues.append(
            ValidationIssue(
                "warning", "name-fallback", collection, "顶层 name 缺失，回退文件名"
            )
        )

    entries: list[ManifestEntry] = []
    seen_ids: set[str] = set()
    specs = raw.get("examples")
    if not isinstance(specs, list):
        report.issues.append(
            ValidationIssue(
                "error", "examples-missing", collection, "缺少 examples 数组"
            )
        )
        specs = []
    for i, spec in enumerate(specs):
        if not isinstance(spec, dict):
            report.issues.append(
                ValidationIssue(
                    "error", "entry-not-object", f"#{i}", "条目不是对象，被拒收"
                )
            )
            continue
        entry = _build_entry(spec, i, report, seen_ids)
        if entry is not None:
            entries.append(entry)

    return Manifest(
        path=Path(path),
        schema_version=schema_version,
        name=collection,
        description=str(raw.get("description") or ""),
        entries=entries,
        report=report,
        raw=raw,
    )


def resolve_entry_file(
    manifest_path: Path, entry: ManifestEntry, data_root: Path
) -> Path | None:
    """把 ``file`` 解析成真实路径；越界或字段缺失返回 None。

    ``data_root`` = 集合树根（内置 = 仓库根；用户集合 = user_examples 的父目录）。
    契约 §2.3 的"解析后仍在集合根内"校验落在这里：``../topics/x.py`` 这类原位引用合法，
    而任何解析到集合树之外的路径都拒绝（否则 file 会变成数据外泄通道）。
    """
    if not entry.file:
        return None
    root = Path(data_root).resolve()
    candidate = (Path(manifest_path).parent / entry.file).resolve()
    if not candidate.is_relative_to(root):  # py3.9+：越界即拒
        return None
    return candidate


def entry_code(
    manifest_path: Path, entry: ManifestEntry, data_root: Path
) -> str | None:
    """取条目源码：v2 读真实文件，v1 兼容期读内联 code。读取失败返回 None。"""
    path = resolve_entry_file(manifest_path, entry, data_root)
    if path is None:
        return entry.code
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return entry.code
