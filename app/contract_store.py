"""契约 v2 存储：清单 + 真实源码树 + 按需运行工作区（契约 §3–§4）。

与 v1（``json_examples.ExampleStore``）的关键差别：
- **启动零写盘**：load 只读清单与真实文件建索引，不物化任何东西；
- **按需工作区**：``ensure_workspace`` 是唯一落盘入口（运行/资源/上传先经它），
  基线刷新只动基线文件，**用户资产与运行产物永不删**；
- 清单是真相源：保存编辑直接原子写真实文件，不再回写内联 code。

派生事实（质量分 / 风险 / 静态状态 / import 清单 / 内容哈希）走**烘焙索引**（契约 §3.2）：
构建期用 ``bake_facts`` 产出 ``json_examples/facts.json`` 随包分发，load 时逐文件哈希校验命中即用；
失配条目当场重算并写缓存根，下次启动即命中。未迁移的 v1 条目回退惰性计算。
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from . import facts as facts_mod
from .importer import extract_imports
from .logger import get_logger
from .manifest_v2 import Manifest, ManifestEntry, entry_code, load_manifest, resolve_entry_file
from .models import ExampleItem
from .quality import QualityScorer
from .run_status import MISSING_DEPS, ModuleIndex, compute_run_status
from .security import RiskLevel

WORKSPACE_DIRNAME = ".json_examples_cache"
WORKSPACE_VERSION = "v2"
DEFAULT_MAX_BYTES = 1024**3  # 契约 §4.4：默认 1GiB

# 静态终态：不需要再过"缺依赖"维度的状态（与 compute_run_status 的优先级一致）
_TERMINAL_STATIC = facts_mod.TERMINAL_STATIC


@dataclass
class WorkspacePlan:
    """工作区落盘计划（ensure_workspace 的中间产物，便于测试与日志）。"""

    safe_name: str
    base_files: list[Path] = field(default_factory=list)
    target: Path | None = None


def safe_name(raw: str) -> str:
    """目录名规范化：干净键保持原名，有损替换时追加内容哈希（按构造无碰撞）。"""
    cleaned = "".join(c if c.isalnum() or c in "-_." else "_" for c in raw)
    if cleaned == raw and cleaned not in ("", ".", ".."):
        return cleaned
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
    return f"{cleaned or 'item'}-{digest}"


_VALID_REQ = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# 与渲染层 filter-engine.ts 的 STDLIB 逐字一致：两边口径不同会让 import 标签漂移
_STDLIB = {
    "abc", "argparse", "ast", "asyncio", "base64", "bisect", "calendar", "collections",
    "concurrent", "configparser", "contextlib", "copy", "csv", "ctypes", "dataclasses",
    "datetime", "decimal", "difflib", "email", "enum", "fnmatch", "functools", "glob",
    "gzip", "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect", "io",
    "itertools", "json", "logging", "math", "multiprocessing", "operator", "os", "pathlib",
    "pickle", "pprint", "queue", "random", "re", "shutil", "signal", "socket", "sqlite3",
    "statistics", "string", "struct", "subprocess", "sys", "tempfile", "textwrap",
    "threading", "time", "traceback", "types", "typing", "unittest", "urllib", "uuid",
    "warnings", "weakref", "xml", "zipfile",
}


def _bare_pkg(spec: str) -> str:
    return spec.split(";")[0].split("==")[0].split(">=")[0].split("[")[0].strip()


def _atomic_write_text(path: Path, text: str) -> None:
    """tmp + os.replace 原子写；中途失败必须清掉 tmp（契约 §7 G2：无 .tmp 残留）。"""
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


class ContractStore:
    """v2 读写入口。所有路径参数由调用方注入（打包版 APP_DIR 只读，用可写根）。"""

    def __init__(
        self,
        collection_dir: Path,
        data_root: Path,
        workspace_root: Path,
        user_dir: Path | None = None,
    ) -> None:
        self.collection_dir = Path(collection_dir).resolve()
        self.data_root = Path(data_root).resolve()
        self.workspace_root = Path(workspace_root).resolve() / WORKSPACE_VERSION
        self.user_dir = Path(user_dir).resolve() if user_dir else None
        self._index: dict[str, ExampleItem] = {}
        self._root: ExampleItem | None = None
        self._manifests: dict[str, Manifest] = {}
        self._scorer = QualityScorer()
        self._risk_findings: dict[str, list[dict]] = {}
        self._import_tags: dict[str, list[str]] = {}
        self._theme_key: dict[str, str | None] = {}
        self._run_status: dict[str, str] = {}
        self._module_index: ModuleIndex | None = None
        self._categories: tuple[str, ...] = ("topics", "tools", "projects")
        # 派生事实（契约 §3.2）：id → 烘焙条目；facts_source 记录本次是从哪来的
        self._facts: dict[str, Any] = {}
        self._facts_ready = False
        self.facts_source = "unloaded"

    @classmethod
    def for_base_dir(cls, base_dir: Path, cache_dir: Path | None = None, user_dir: Path | None = None) -> "ContractStore":
        """按 v1 的 (base_dir, cache_dir, user_dir) 口径构造，供测试与迁移期平滑切换。"""
        base = Path(base_dir).resolve()
        return cls(
            collection_dir=base / "json_examples",
            data_root=base,
            workspace_root=(Path(cache_dir) if cache_dir else base / WORKSPACE_DIRNAME),
            user_dir=user_dir,
        )

    # ------------------------------------------------------------------ 加载
    def load(self) -> ExampleItem:
        """读清单 + 真实树建索引（契约 §3.1：零写盘，派生事实走烘焙索引）。"""
        root = ExampleItem(name="Python 示例仓库", path=self.data_root, is_dir=True, category="root", repo_root=self.data_root)
        self._index.clear()
        self._manifests.clear()
        for manifest_path in self._iter_manifests():
            collection = self._load_collection(manifest_path)
            if collection is not None:
                root.children.append(collection)
        self._root = root
        self._refresh_categories()
        self._adopt_facts()
        return root

    # ------------------------------------------------------------ 烘焙事实索引
    def facts_shipped_path(self) -> Path:
        """随包分发的烘焙事实（构建期产出，打包版只读）。"""
        return self.collection_dir / facts_mod.FACTS_FILENAME

    def facts_cache_path(self) -> Path:
        """本机重建后的缓存副本（开发/失配时写这里，不污染真相源）。"""
        return self.workspace_root / facts_mod.FACTS_FILENAME

    def _adopt_facts(self) -> None:
        """载入派生事实索引：随包烘焙优先，其次缓存副本；都没有才全量重算。

        失配不是"全丢"：逐条按文件哈希判定，命中条目直接复用、变化条目当场重算，
        结果与全量重算逐字段等价（adopt 与 build 的等价性由测试钉住）。
        """
        # 先置位再计算：重算条目会经 import_tags/theme_key 回读事实，
        # 置位可避免"载入中"状态下再次进入本函数（无限递归）。
        self._facts_ready = True
        self._facts = {}
        for source, path in (("shipped", self.facts_shipped_path()), ("cache", self.facts_cache_path())):
            data = facts_mod.load(path)
            if data is None:
                continue
            items, status = facts_mod.adopt(data, self)
            self._facts = items
            self._facts_ready = True
            self.facts_source = source if status == "hit" else f"{source}-partial"
            if status != "hit":
                self._persist_facts()
            get_logger(__name__).info(
                "派生事实索引：来源=%s 状态=%s 条目=%d 指纹=%s",
                source,
                status,
                len(items),
                facts_mod.fingerprint(facts_mod.make_data(self, items)),
            )
            return
        data = facts_mod.build(self)
        self._facts = data["items"]
        self._facts_ready = True
        self.facts_source = "rebuilt"
        self._persist_facts(data)
        get_logger(__name__).info("派生事实索引：全新烘焙 %d 条", len(self._facts))

    def _ensure_facts(self) -> None:
        """取事实前确保已载入（load 之外的入口，如直接构造 store 的测试）。"""
        if not self._facts_ready:
            self._adopt_facts()

    def _persist_facts(self, data: dict[str, Any] | None = None) -> None:
        """把事实写进缓存根（best-effort：打包版缓存根不可写时只记日志）。"""
        payload = data if data is not None else facts_mod.make_data(self, self._facts)
        try:
            self.workspace_root.mkdir(parents=True, exist_ok=True)
            self._write_atomic(
                self.facts_cache_path(),
                lambda tmp: tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8"),
            )
        except OSError as e:
            get_logger(__name__).warning("派生事实索引写入缓存失败: %s", e)

    def bake_facts(self, dest: Path | None = None) -> dict[str, Any]:
        """构建期全量烘焙；``dest`` 给定则落盘（工具入口用）。"""
        data = facts_mod.build(self)
        if dest is not None:
            dest.parent.mkdir(parents=True, exist_ok=True)
            self._write_atomic(
                dest, lambda tmp: tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            )
        return data

    def fact(self, item: ExampleItem, key: str) -> Any:
        """读单条烘焙事实字段；未命中返回 None（调用方回退惰性计算）。"""
        entry = self._fact_entry(item)
        return entry.get(key) if entry is not None else None

    def _fact_entry(self, item: ExampleItem) -> dict[str, Any] | None:
        """单条烘焙事实整行；无烘焙数据返回 None。

        「有事实但值为 None」（如 theme 未命中主题）与「没有事实」必须区分，
        故取码走整行而不是 ``fact(item, key) is not None``。
        """
        self._ensure_facts()
        entry = self._facts.get(item.json_id or str(item.path))
        return entry if isinstance(entry, dict) else None

    def _iter_manifests(self) -> list[Path]:
        """清单文件列表（排除烘焙事实文件——它与清单同目录但不是集合）。"""
        paths = (
            [p for p in sorted(self.collection_dir.glob("*.json")) if p.name != facts_mod.FACTS_FILENAME]
            if self.collection_dir.is_dir()
            else []
        )
        if self.user_dir and self.user_dir.is_dir():
            paths.extend(p for p in sorted(self.user_dir.glob("*.json")) if p.name != facts_mod.FACTS_FILENAME)
        return paths

    def _load_collection(self, manifest_path: Path) -> ExampleItem | None:
        try:
            manifest = load_manifest(manifest_path)
        except (OSError, ValueError) as e:
            get_logger(__name__).error("读取清单失败 %s: %s", manifest_path, e)
            return None
        if manifest.report.issues:
            by_code: dict[str, int] = {}
            for issue in manifest.report.issues:
                by_code[issue.code] = by_code.get(issue.code, 0) + 1
            summary = ", ".join(f"{code}×{n}" for code, n in sorted(by_code.items()))
            get_logger(__name__).log(
                40 if manifest.report.errors else 30, "清单校验 %s: %s", manifest_path.name, summary
            )
        if not manifest.entries:
            return None

        coll_root = ExampleItem(name=f"📦 {manifest.name}", path=manifest_path, is_dir=True, category="json")
        for entry in manifest.entries:
            item = self._build_item(manifest, entry, coll_root)
            if item is not None:
                coll_root.children.append(item)
        if not coll_root.children:
            return None
        return coll_root

    def _build_item(self, manifest: Manifest, entry: ManifestEntry, coll_root: ExampleItem) -> ExampleItem | None:
        real_path = resolve_entry_file(manifest.path, entry, self._root_for(manifest.path))
        if real_path is None and not entry.code:
            # 契约 §2.3：既无 file（v2）也无内联 code（v1 兼容）＝没有内容来源，
            # 与 v1 一致跳过该条（记警告，fail-visible 而非收进树里当空壳示例）
            get_logger(__name__).warning("条目无内容来源，已跳过: %s/%s", manifest.name, entry.id)
            return None
        if real_path is None:
            # v1 兼容期：清单只有内联 code 时以计划路径占位（迁移前仍可浏览/运行）
            real_path = (self.workspace_root / safe_name(entry.id) / entry.name).resolve()
        item = ExampleItem(
            name=entry.name,
            path=real_path,
            is_dir=False,
            category=entry.category,
            source="json",
            code=None,  # v2：code 只在需要时按需读取
            json_id=entry.id,
            json_file=manifest.path,
            description=entry.description,
            json_title=entry.title,
        )
        item.parent = coll_root
        item.tags = list(entry.tags)
        # dir 字段退役：项目分组键改为从真实路径相对集合树根派生（契约 §2.2）
        item.source_dir = entry.source_dir or self._project_key(item.path, manifest.path)
        item.quality_score = None
        self._index[entry.id] = item
        self._manifests[entry.id] = manifest
        return item

    def _root_for(self, manifest_path: Path) -> Path:
        """该清单的集合树根：内置 = 仓库根；用户集合 = user_examples 的父目录（契约 §2.3）。

        打包版的用户集合在可写根（userData）下，与仓库根不同源；
        用同一个根去解析会让用户集合的 ``file`` 全部判越界而被丢弃。
        """
        if self.user_dir is not None and manifest_path.parent == self.user_dir:
            return self.user_dir.parent
        return self.data_root

    def _project_key(self, real_path: Path, manifest_path: Path) -> str | None:
        """项目分组键：topics/tools/projects 下的一级（或二级）目录相对路径。

        入参已是规范化路径（resolve_entry_file 的产物），不再做 realpath——
        1500 次多余 lstat 是冷启动预算里最容易被忽视的一笔开销。
        """
        try:
            rel = real_path.relative_to(self._root_for(manifest_path))
        except (OSError, ValueError):
            return None
        parts = rel.parts
        if len(parts) >= 3 and parts[0] in ("topics", "tools", "projects"):
            return "/".join(parts[:2])
        if len(parts) >= 2 and parts[0] in ("topics", "tools", "projects"):
            return parts[0]
        return None

    @property
    def index(self) -> dict[str, ExampleItem]:
        return self._index

    @property
    def root(self) -> ExampleItem | None:
        return self._root

    @property
    def categories(self) -> tuple[str, ...]:
        return self._categories

    def _refresh_categories(self) -> None:
        cats = {"topics", "tools", "projects"}
        for item in self._index.values():
            if item.category:
                cats.add(item.category)
        self._categories = tuple(sorted(cats))

    def is_user_collection(self, manifest_path: Path | None) -> bool:
        if manifest_path is None or self.user_dir is None:
            return False
        try:
            return Path(manifest_path).resolve().is_relative_to(self.user_dir)
        except (OSError, ValueError):
            return False

    # ------------------------------------------------------------------ 读取
    def get_code(self, item: ExampleItem) -> str:
        """取示例源码：v2 读真实文件，v1 兼容期读内联 code（契约 §2.4）。"""
        entry = self._entry_of(item)
        if entry is None:
            return item.code or ""
        manifest = self._manifests[item.json_id or ""]
        return entry_code(manifest.path, entry, self._root_for(manifest.path)) or ""

    def _entry_of(self, item: ExampleItem) -> ManifestEntry | None:
        manifest = self._manifests.get(item.json_id or "")
        if manifest is None:
            return None
        for entry in manifest.entries:
            if entry.id == item.json_id:
                return entry
        return None

    def search(self, query: str, limit: int = 50) -> list[dict[str, str]]:
        """服务端检索：元数据内存匹配 + code 按需读文件（契约 §5）。"""
        q = (query or "").strip().lower()
        if not q:
            return []
        hits: list[dict[str, str]] = []
        for item in self._index.values():
            reason = ""
            if q in item.name.lower() or q in (item.json_title or "").lower():
                reason = "name"
            elif any(q in t.lower() for t in item.tags):
                reason = "tag"
            elif q in (item.description or "").lower():
                reason = "description"
            elif q in self.get_code(item).lower():
                reason = "code"
            if reason:
                hits.append({"id": item.json_id or "", "reason": reason})
                if len(hits) >= limit:
                    break
        return hits

    @property
    def _checker(self):  # type: ignore[no-untyped-def]
        """扫描器按需读取（不缓存实例）：与质量评分共用同一个，护栏据此验证"扫描异常不 fail-open"。"""
        return self._scorer.security_checker

    # ------------------------------------------------------------------ 派生分类（列表下发的派生事实）
    def import_tags(self, item: ExampleItem) -> list[str]:
        """第三方 import 清单（去 stdlib、顶层模块名、小写排序）。

        与渲染层 ``FilterEngine.extractImportTags`` 同口径；v2 不再下发 code，
        改由服务端算好随列表下发（契约 §3.2 / §5）。优先取烘焙事实。
        """
        key = item.json_id or str(item.path)
        if key not in self._import_tags:
            baked = self.fact(item, "imports")
            if baked is not None:
                self._import_tags[key] = list(baked)
                return self._import_tags[key]
            mods = extract_imports(self.get_code(item))
            self._import_tags[key] = sorted(
                {m.split(".")[0].lower() for m in mods if m and m.split(".")[0].lower() not in _STDLIB}
            )
        return self._import_tags[key]

    def theme_key(self, item: ExampleItem) -> str | None:
        """命中的主题 key（首个匹配，与渲染层 themes.ts 的谓词顺序/语义逐条对齐）。

        主题谓词里既有 import 判定也有正文子串判定（如 turtle），因此判据必须留在
        能读到源码的一侧——服务端算好下发，渲染层只认结果（否则分类会随"是否下发 code"漂移）。
        """
        key = item.json_id or str(item.path)
        if key in self._theme_key:
            return self._theme_key[key]
        entry = self._fact_entry(item)
        if entry is not None and "theme" in entry:
            self._theme_key[key] = entry["theme"]
            return self._theme_key[key]
        code = self.get_code(item)
        code_lower = code.lower()
        name = item.name.lower()
        desc = (item.description or "").lower()
        tags = " ".join(item.tags).lower()
        not_project = item.name != "__init__.py" and item.category != "projects"
        found: str | None = None
        if "turtle" in name or "turtle" in desc or "turtle" in code_lower or "turtle" in tags:
            found = "turtle"
        elif not_project and re.search(r"^\s*(?:import|from)\s+pygame\b", code, re.MULTILINE):
            found = "games"
        elif not_project and re.search(r"^\s*(?:import|from)\s+cv2\b", code, re.MULTILINE):
            found = "opencv"
        elif not_project and re.search(r"^\s*(?:import|from)\s+(?:PIL|Pillow)\b", code, re.MULTILINE):
            found = "images"
        elif not_project and re.search(r"\b(matplotlib|pyplot|pandas)\b", code):
            found = "viz"
        self._theme_key[key] = found
        return found

    # ------------------------------------------------------------------ 质量/风险/状态
    def _analysis_item(self, item: ExampleItem) -> ExampleItem:
        """派生事实的分析对象：v2 用真实文件；v1 兼容期先确保工作区（code→文件）。"""
        if self._is_v2_item(item) and item.path.is_file():
            return item
        workspace = self.ensure_workspace(item)
        candidate = (workspace / item.name) if workspace else None
        if candidate and candidate.is_file():
            return dataclasses.replace(item, path=candidate)
        return item

    def ensure_quality_score(self, item: ExampleItem) -> int:
        """质量分：优先取烘焙事实；未命中才按路径读盘评分。"""
        if item.quality_score is not None:
            return item.quality_score
        baked = self.fact(item, "quality")
        if baked is not None:
            item.quality_score = int(baked)
            return item.quality_score
        try:
            item.quality_score = self._scorer.score(self._analysis_item(item)).score
        except Exception:  # noqa: BLE001 - 评分失败不应阻断使用
            item.quality_score = 0
        return item.quality_score

    def ensure_risk_findings(self, item: ExampleItem) -> list[dict]:
        """HIGH 风险明细（与运行前确认弹窗同源）；优先取烘焙事实，未命中才现算。"""
        key = item.json_id or str(item.path)
        if key not in self._risk_findings:
            baked = self.fact(item, "risk_findings")
            if baked is not None:
                self._risk_findings[key] = list(baked)
                return self._risk_findings[key]
            report = self._checker.check(self._analysis_item(item).path, key, content=self.get_code(item))
            self._risk_findings[key] = [{"description": r.description, "category": r.category} for r in report.risk_details if r.level == RiskLevel.HIGH]
        return self._risk_findings[key]

    def ensure_risk_high(self, item: ExampleItem) -> bool:
        baked = self.fact(item, "risk_high")
        if baked is not None:
            return bool(baked)
        return bool(self.ensure_risk_findings(item))

    def ensure_run_status(self, item: ExampleItem) -> str:
        key = item.json_id or str(item.path)
        if key in self._run_status:
            return self._run_status[key]
        static = self.fact(item, "static")
        if static is not None:
            # 烘焙的是静态态；缺依赖维度依赖运行环境，运行时用模块索引合成
            status = self._combine_status(static, self.fact(item, "deps") or [])
        else:
            status = compute_run_status(
                self.get_code(item),
                example_id=item.json_id,
                local_dirs=[self._analysis_item(item).path.parent],
                checker=self._checker,
                module_index=self._module_index,
            )
        self._run_status[key] = status
        return status

    def _combine_status(self, static: str, deps: list[str]) -> str:
        """静态态 + 模块索引 → 最终状态（优先级与 compute_run_status 一致）。"""
        if static in _TERMINAL_STATIC:
            return static
        if self._module_index is not None and self._module_index.available:
            if self._module_index.missing_modules(set(deps)):
                return MISSING_DEPS
        return static

    def set_module_python(self, python_exe: str | None) -> None:
        self._module_index = ModuleIndex(python_exe) if python_exe else None
        self._run_status.clear()

    def invalidate(self, item: ExampleItem) -> None:
        """编辑后失效该示例的派生事实：内存缓存 + 烘焙条目一并丢弃。

        烘焙文件不立即重写（契约 §3.2：下次启动按哈希失配重算），
        但本进程内必须立刻反映新内容——后续访问走惰性计算路径。
        """
        key = item.json_id or str(item.path)
        self._run_status.pop(key, None)
        self._risk_findings.pop(key, None)
        self._import_tags.pop(key, None)
        self._theme_key.pop(key, None)
        self._facts.pop(key, None)
        item.quality_score = None

    # ------------------------------------------------------------------ 工作区
    def workspace_of(self, item: ExampleItem) -> Path:
        return self.workspace_root / safe_name(item.json_id or item.name)

    def _is_v2_item(self, item: ExampleItem) -> bool:
        """是否已迁移到 v2（清单条目带 file）。

        不能用 item.path 是否存在判断：v1 兼容期 item.path 指向"计划中的工作区位置"，
        工作区一旦建过就会让 is_file() 为真，从而把工作区误当真实源。
        """
        entry = self._entry_of(item)
        return bool(entry and entry.file)

    def _source_dir(self, item: ExampleItem) -> Path | None:
        """基线文件的来源目录：v2 = 真实文件的父目录；v1 兼容 = 清单 dir 指向的源目录。

        仍受集合树边界约束（越界一律不认），因此兼容期也不会把仓库外内容拷进工作区。
        """
        if self._is_v2_item(item) and item.path.is_file():
            return item.path.parent
        entry = self._entry_of(item)
        if entry and entry.source_dir:
            root = self._root_for(item.json_file or self.collection_dir)
            candidate = (root / entry.source_dir).resolve()
            if candidate.is_dir() and candidate.is_relative_to(root):
                return candidate
        return None

    def _baseline_files(self, item: ExampleItem) -> dict[str, str]:
        """基线文件清单：{文件名: sha256}。

        - v2：目标 .py 真实存在，连同同目录兄弟文件（.py/数据）一起进基线；
        - v1 兼容期：真实文件尚未外移，用清单里的内联 code 当基线（迁移后自动切到文件）。
        清单 JSON 与 .backup 不算基线。
        """
        files: dict[str, str] = {}
        source_dir = self._source_dir(item)
        v2 = self._is_v2_item(item)
        if source_dir is not None:
            for sibling in sorted(source_dir.iterdir()):
                if not sibling.is_file() or sibling.suffix == ".json" or sibling.name.startswith("."):
                    continue
                content = sibling.read_bytes()
                if sibling.name == item.name and not v2:
                    # v1 兼容期：目标文件的基线取清单内联 code（源文件可能尚未外移）
                    content = self.get_code(item).encode("utf-8")
                files[sibling.name] = hashlib.sha256(content).hexdigest()
            if item.name not in files:
                files[item.name] = hashlib.sha256(item.path.read_bytes() if v2 else self.get_code(item).encode("utf-8")).hexdigest()
            return files
        code = self.get_code(item)
        if code:
            files[item.name] = hashlib.sha256(code.encode("utf-8")).hexdigest()
        return files

    def base_key(self, item: ExampleItem) -> str:
        h = hashlib.sha256()
        entry = self._entry_of(item)
        for name, digest in sorted(self._baseline_files(item).items()):
            h.update(name.encode("utf-8"))
            h.update(digest.encode("utf-8"))
        for req in sorted(entry.requirements if entry else []):
            h.update(req.encode("utf-8"))
        return h.hexdigest()

    def ensure_workspace(self, item: ExampleItem) -> Path | None:
        """幂等落盘：把基线文件放到工作区并保证与真实文件一致；返回工作区目录。

        - 清单命中且 base_key 一致 → 只补齐缺失/被改坏的基线文件；
        - base_key 变化 → 按基线清单做差集：删**旧基线**、拷新基线；
        - 不在基线清单里的文件（用户资产、运行产物）永不删除。
        """
        try:
            workspace = self.workspace_of(item)
            workspace.mkdir(parents=True, exist_ok=True)
            baseline = self._baseline_files(item)
            key = self.base_key(item)
            manifest_file = workspace / ".manifest.json"
            previous: dict = {}
            if manifest_file.is_file():
                try:
                    previous = json.loads(manifest_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    previous = {}

            # 基线刷新：删掉不在新基线里的**旧基线文件**（用户资产不在其中，天然被保留）
            for stale in previous.get("files", {}):
                if stale not in baseline:
                    (workspace / stale).unlink(missing_ok=True)

            for name, digest in baseline.items():
                dest = workspace / name
                if dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == digest:
                    continue  # 已一致：不重复写（避免无谓改动与 mtime 抖动）
                source_dir = self._source_dir(item)
                source = (source_dir / name) if source_dir else None
                if source is not None and source.is_file() and not (name == item.name and not self._is_v2_item(item)):
                    self._copy_atomic(source, dest)
                elif name == item.name:
                    # v1 兼容期：真实文件还没外移，用清单内联 code 落进工作区
                    self._write_atomic(dest, lambda tmp: tmp.write_text(self.get_code(item), encoding="utf-8"))

            reqs = [r for r in (self._entry_of(item).requirements if self._entry_of(item) else []) if _VALID_REQ.match(_bare_pkg(r))]
            if reqs:
                req_file = workspace / "requirements.txt"
                # 合并：工作区里可能已有用户/前次写入的清单，按行去重保序；同样走原子唯一 tmp
                merged = (
                    list(dict.fromkeys([*req_file.read_text(encoding="utf-8").splitlines(), *reqs]))
                    if req_file.is_file()
                    else reqs
                )
                self._write_atomic(req_file, lambda tmp: tmp.write_text("\n".join(x for x in merged if x.strip()) + "\n", encoding="utf-8"))

            self._write_atomic(
                manifest_file,
                lambda tmp: tmp.write_text(json.dumps(
                    {
                        "contract": 2,
                        "base_key": key,
                        "files": baseline,
                        "requirements": reqs,
                    },
                    ensure_ascii=False,
                    indent=1,
                ) + "\n", encoding="utf-8"),
            )
            return workspace
        except OSError as e:
            get_logger(__name__).error("准备工作区失败 %s: %s", item.json_id, e)
            return None

    def run_pythonpath(self, item: ExampleItem) -> list[str]:
        """运行时的 sys.path：工作区目录 + 其向上到工作区根的祖先（兄弟/包导入）。"""
        workspace = self.workspace_of(item)
        paths = [str(workspace)]
        cur = workspace.parent
        while cur.is_relative_to(self.workspace_root):
            paths.append(str(cur))
            if cur == self.workspace_root:
                break
            cur = cur.parent
        return paths

    @staticmethod
    def _write_atomic(dest: Path, write: "Callable[[Path], None]") -> None:
        """原子写：临时文件名唯一（并发调用不得互相踩踏），写完 os.replace。"""
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), prefix=dest.name + ".", suffix=".tmp")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            write(tmp)
            os.replace(tmp, dest)
        finally:
            tmp.unlink(missing_ok=True)

    @classmethod
    def _copy_atomic(cls, src: Path, dest: Path) -> None:
        cls._write_atomic(dest, lambda tmp: shutil.copy2(src, tmp))

    # ------------------------------------------------------------------ 写入
    def save_item(self, item: ExampleItem, new_code: str) -> bool:
        """保存编辑：原子写真实文件（v2 不再回写内联 code，契约 §2.2）。

        v1 兼容窗口内清单未迁移（无真实文件）→ **只读**，明确拒绝而不是写坏工作区。
        """
        if not self._is_v2_item(item):
            get_logger(__name__).warning("该集合尚未迁移到契约 v2，编辑只读: %s", item.json_id)
            return False
        try:
            _atomic_write_text(item.path, new_code)
        except OSError as e:
            get_logger(__name__).error("保存失败 %s: %s", item.json_id, e)
            return False
        self.invalidate(item)
        # 工作区基线立即跟随（下次 ensure_workspace 也会按哈希自愈）
        workspace = self.workspace_of(item)
        if workspace.is_dir():
            try:
                self._copy_atomic(item.path, workspace / item.path.name)
            except OSError as e:
                get_logger(__name__).warning("工作区同步失败（下次进入会自愈）: %s", e)
        return True

    def delete_user_example(self, item: ExampleItem) -> bool:
        """删除用户示例：清单条目 + 真实文件 + 工作区三处同步清理（契约 §5）。

        内置集合（不在 user_dir 下）拒绝删除。
        """
        manifest_path = item.json_file
        if not self.is_user_collection(manifest_path) or manifest_path is None:
            return False
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        entries = [e for e in data.get("examples", []) if str(e.get("id")) != item.json_id]
        if len(entries) == len(data.get("examples", [])):
            return False
        data["examples"] = entries
        try:
            if entries:
                _atomic_write_text(manifest_path, json.dumps(data, ensure_ascii=False, indent=1) + "\n")
            else:
                manifest_path.unlink()  # 空集合：清单一并移除
            if item.path.is_file() and item.path.resolve().is_relative_to(self.user_dir):
                item.path.unlink()
            if not entries:
                # 源码删空后集合目录也一并收掉：否则下次导入同名目录会被迫改名 _2。
                # 目录里还有用户上传的资源时保留（那是有内容要留存，改名才安全）。
                collection_dir = item.path if item.path.is_dir() else item.path.parent
                try:
                    if collection_dir.is_dir() and not any(collection_dir.iterdir()):
                        collection_dir.rmdir()
                except OSError:
                    pass
            shutil.rmtree(self.workspace_of(item), ignore_errors=True)
        except OSError as e:
            get_logger(__name__).error("删除用户示例失败 %s: %s", item.json_id, e)
            return False
        self._index.pop(item.json_id or "", None)
        self._manifests.pop(item.json_id or "", None)
        self.invalidate(item)
        return True

    # ------------------------------------------------------------------ 治理
    def workspace_usage(self) -> int:
        total = 0
        if self.workspace_root.is_dir():
            for path in self.workspace_root.rglob("*"):
                if path.is_file():
                    total += path.stat().st_size
        return total

    def prune(self, max_bytes: int = DEFAULT_MAX_BYTES) -> int:
        """超限按 last_used 从旧到新淘汰（含用户资产的条目仅在无干净候选时才动）。"""
        if not self.workspace_root.is_dir():
            return 0
        entries: list[tuple[float, Path, bool]] = []
        for workspace in self.workspace_root.iterdir():
            if not workspace.is_dir():
                continue
            manifest_file = workspace / ".manifest.json"
            last_used = manifest_file.stat().st_mtime if manifest_file.is_file() else workspace.stat().st_mtime
            known = set()
            if manifest_file.is_file():
                try:
                    known = set(json.loads(manifest_file.read_text(encoding="utf-8")).get("files", {}))
                except (OSError, json.JSONDecodeError):
                    known = set()
            has_assets = any(p.is_file() and p.name not in known and p.name != ".manifest.json" for p in workspace.iterdir())
            entries.append((last_used, workspace, has_assets))
        entries.sort()
        removed = 0
        total = self.workspace_usage()
        for _last_used, workspace, has_assets in entries:
            if total <= max_bytes:
                break
            if has_assets:
                continue  # 有用户资产：先跳过，只在没有干净候选时才考虑
            size = sum(p.stat().st_size for p in workspace.rglob("*") if p.is_file())
            shutil.rmtree(workspace, ignore_errors=True)
            total -= size
            removed += 1
        if total > max_bytes:
            for _last_used, workspace, has_assets in entries:
                if total <= max_bytes:
                    break
                if not has_assets:
                    continue
                size = sum(p.stat().st_size for p in workspace.rglob("*") if p.is_file())
                get_logger(__name__).warning("无干净候选，淘汰含用户资产的工作区: %s", workspace.name)
                shutil.rmtree(workspace, ignore_errors=True)
                total -= size
                removed += 1
        return removed

    def collect_garbage(self) -> int:
        """孤儿回收：工作区不在当前索引键集合中就清理（后台缓慢进行，有日志）。

        含用户资产（不在账本里的上传文件/运行产物）的孤儿**不静默删除**：
        用户的东西只能由用户显式清理（契约 §4.4），这里只计数并记日志。
        """
        if not self.workspace_root.is_dir():
            return 0
        alive = {safe_name(key) for key in self._index}
        removed = 0
        kept = 0
        for workspace in self.workspace_root.iterdir():
            if not workspace.is_dir() or workspace.name in alive:
                continue
            if self._has_user_assets(workspace):
                kept += 1
                continue
            shutil.rmtree(workspace, ignore_errors=True)
            removed += 1
        if removed:
            get_logger(__name__).info("孤儿工作区回收 %d 个", removed)
        if kept:
            get_logger(__name__).warning("孤儿工作区含用户资产，保留待人工清理: %d 个", kept)
        return removed

    @staticmethod
    def _has_user_assets(workspace: Path) -> bool:
        """工作区里是否存在账本之外的文件（用户上传/运行产物）。

        没有账本时按"有资产"处理（保守：宁可留着，也不静默删掉来历不明的文件）。
        """
        ledger = workspace / ".manifest.json"
        if not ledger.is_file():
            return any(p.is_file() for p in workspace.rglob("*"))
        try:
            known = set(json.loads(ledger.read_text(encoding="utf-8")).get("files", {}))
        except (OSError, json.JSONDecodeError):
            return True
        return any(
            p.is_file() and p.name not in known and p.name != ".manifest.json"
            for p in workspace.rglob("*")
        )

    def user_assets(self, item: ExampleItem) -> list[Path]:
        """工作区里的用户资产与运行产物（不在基线清单中的文件）。"""
        workspace = self.workspace_of(item)
        if not workspace.is_dir():
            return []
        try:
            known = set(json.loads((workspace / ".manifest.json").read_text(encoding="utf-8")).get("files", {}))
        except (OSError, json.JSONDecodeError):
            known = set()
        return [p for p in sorted(workspace.iterdir()) if p.is_file() and p.name not in known and p.name != ".manifest.json"]


def iter_manifests(store: ContractStore) -> Iterable[Path]:
    return store._iter_manifests()
