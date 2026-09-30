"""统一示例数据源（JSON 为唯一真相源）。

全面改造后，所有示例均来自 JSON 集合文件（``desktop-app/json_examples/*.json``）。
每个示例的代码物化（materialize）到本地缓存目录后再运行/评分/编辑；若示例声明了
``requirements``，则在同一目录生成 ``requirements.txt``，运行时装入项目共享虚拟环境。
缓存文件可随时由 JSON 重建，不视为源码。

物化策略：
- 若示例在 JSON 中记录了原始目录 ``dir``（迁移脚本生成），则把**整个原始目录**
  （含同目录兄弟模块、数据文件、requirements.txt）拷贝到缓存，再在该重建的目录结构里
  用 JSON 中的代码覆盖运行目标文件。这样示例原本依赖的兄弟模块与相对数据路径都能正常工作。
- 若示例无 ``dir``（如手写的基础示例），则退化为单文件物化。

搜索、加载、保存、依赖（requirements）统一由此模块处理。
"""

import ast
import json
import os
import re
import shutil
import warnings
from pathlib import Path

from .logger import get_logger
from .models import ExampleItem
from .quality import QualityScorer
from .run_status import (
    BROKEN,
    EMPTY,
    MISSING_DEPS,
    RISKY,
    RUNNABLE,
    ModuleIndex,
    is_empty_body,
    parse_code,
    third_party_imports,
)
from .security import RiskLevel

SKIP_DIRS = {"__pycache__", ".git", ".venv", "node_modules", ".mypy_cache", ".pytest_cache"}

# 合法 PyPI 包名（不含版本约束部分）：用于丢弃迁移数据中的乱码/非法包名
_VALID_PKG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")


class ExampleStore:
    """基于 JSON 示例集的统一数据源。"""

    COLLECTION_DIRNAME = "json_examples"
    CACHE_DIRNAME = ".json_examples_cache"
    DEFAULT_CATEGORIES = ("topics", "tools", "projects")

    def __init__(
        self,
        base_dir: Path | None = None,
        cache_dir: Path | None = None,
        user_dir: Path | None = None,
    ) -> None:
        # 默认基础目录为桌面应用根（app 的上一级），避免污染大型项目仓库
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = base_dir.resolve()
        self.collection_dir = self.base_dir / self.COLLECTION_DIRNAME
        # 用户示例集合目录（导入向导产物，可写）：打包版为 userData/user_examples，
        # 开发版由 sidecar 传仓库根下同名目录；与内置库并存加载
        self.user_dir = user_dir.resolve() if user_dir else None
        # 缓存根可注入：打包模式下 APP_DIR（Resources）只读，由 sidecar 把
        # userData 作为可写根传入（venv/物化缓存/运行输出都在可写根下）
        self.cache_dir = (cache_dir or self.base_dir / self.CACHE_DIRNAME).resolve()
        self._scorer = QualityScorer()
        # HIGH 风险明细（description/category），risk_high 徽章与运行前确认共用
        self._risk_findings: dict[str, list[dict]] = {}
        # 可运行性状态缓存：派生数据不落盘，代码变更/模块索引刷新时失效
        self._run_status: dict[str, str] = {}
        self._module_index: ModuleIndex | None = None
        self._root: ExampleItem | None = None
        self._categories: tuple[str, ...] = self.DEFAULT_CATEGORIES
        # 原始仓库根（含 topics/tools/projects），用于整体物化目录
        self._source_root = self._find_repo_root()

    # ------------------------------------------------------------------ 仓库根
    def _find_repo_root(self) -> Path | None:
        """向上查找包含 topics/tools/projects 的目录（即示例原始仓库根）。"""
        current = self.base_dir
        for _ in range(8):
            if all((current / d).is_dir() for d in self.DEFAULT_CATEGORIES):
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    # ------------------------------------------------------------------ 加载
    def load(self) -> ExampleItem:
        """加载所有 JSON 集合，构建并返回根节点（category='root'）。"""
        root = ExampleItem(
            name="Python 示例仓库",
            path=self.base_dir,
            is_dir=True,
            category="root",
            repo_root=self.base_dir,
        )
        if self.collection_dir.exists():
            for json_file in sorted(self.collection_dir.glob("*.json")):
                coll = self._load_collection(json_file)
                if coll is not None:
                    root.children.append(coll)
        # 用户集合目录：不存在则静默跳过（首次启动尚未导入任何示例）
        if self.user_dir is not None and self.user_dir.exists():
            for json_file in sorted(self.user_dir.glob("*.json")):
                coll = self._load_collection(json_file)
                if coll is not None:
                    root.children.append(coll)
        self._root = root
        self._refresh_categories(root)
        return root

    def is_user_collection(self, json_file: Path | None) -> bool:
        """该集合文件是否属于用户集合目录（用户示例可删，内置集合受保护）。"""
        if json_file is None or self.user_dir is None:
            return False
        try:
            return json_file.resolve().is_relative_to(self.user_dir)
        except (OSError, ValueError):
            return False

    def _load_collection(self, json_file: Path) -> ExampleItem | None:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            get_logger(__name__).error("读取 JSON 示例集失败 %s: %s", json_file, e)
            return None

        if not isinstance(data, dict) or not data.get("examples"):
            return None  # 结构非法或空集合（如已删光的用户集合）不生成节点

        coll_name = data.get("name", json_file.stem)
        coll_root = ExampleItem(
            name=f"📦 {coll_name}",
            path=json_file,  # 仅作标识，不参与运行/评分
            is_dir=True,
            category="json",
        )

        for spec in data.get("examples", []):
            if not isinstance(spec, dict) or "code" not in spec:
                continue
            item = self._build_item(spec, json_file)
            if item is not None:
                item.parent = coll_root  # 序列化时经此取所属集合名
                coll_root.children.append(item)
        return coll_root

    def _build_item(self, spec: dict, json_file: Path) -> ExampleItem | None:
        example_id = spec.get("id") or spec.get("name", "")
        if not example_id:
            return None
        code = spec["code"]
        file_name = spec.get("name", f"{example_id}.py")
        dir_rel = spec.get("dir")
        cache_dir, py_path = self._materialize(example_id, file_name, code, spec.get("requirements", []), dir_rel)
        if py_path is None:
            return None

        item = ExampleItem(
            name=file_name,
            path=py_path,
            is_dir=False,
            category=spec.get("category", "topics"),
            source="json",
            code=code,
            json_id=example_id,
            json_file=json_file,
            description=spec.get("description"),
            json_title=spec.get("title"),
        )
        # 记录运行所需 sys.path：原始目录及其所有祖先目录（解析兄弟/包导入）；
        # 用户集合条目没有源目录（dir_rel=None），运行路径仅工作区
        item.run_pythonpath = self._run_pythonpath(dir_rel, cache_dir) if dir_rel and cache_dir else []
        # 原始相对目录透传给渲染层（工具箱按工具项目分组；用户导入条目无此字段）
        item.source_dir = dir_rel
        item.tags = list(spec.get("tags", []))
        # 质量评分改为惰性计算：加载时不做 AST 解析，首次需要时才计算
        # （1349 个示例的 AST 解析在加载时约占 30%+ 耗时，惰性化可显著加快启动）
        item.quality_score = None
        return item

    # --------------------------------------------------------------- 物化
    def _materialize(
        self,
        example_id: str,
        file_name: str,
        code: str,
        requirements: list,
        dir_rel: str | None = None,
    ) -> tuple[Path | None, Path | None]:
        """把代码写成缓存目录中的真实 ``.py`` 文件，返回 (缓存目录, py 路径)。

        - 若 ``dir_rel`` 有效且能定位到原始目录，则先整体拷贝原始目录到缓存，
          再在该目录内用 JSON 代码覆盖目标文件（保留兄弟模块与数据文件）。
        - 若声明了 requirements，则在同一目录生成 requirements.txt，
          供运行时的虚拟环境隔离安装使用。
        - 缓存目录已存在时，比对源目录 mtime，变化则重新拷贝。
        """
        try:
            py_name = file_name if file_name.endswith(".py") else f"{file_name}.py"

            if dir_rel and self._source_root is not None and dir_rel not in ("",):
                orig_dir = (self._source_root / dir_rel).resolve()
                # dir 字段越界防护：绝对路径会被 Path 拼接整体替换、'..' 可跳出
                # 仓库根，二者都会把仓库外目录整个拷入缓存（数据外泄通道）
                if not orig_dir.is_relative_to(self._source_root.resolve()):
                    get_logger(__name__).error("示例 dir 字段越界，拒绝物化: %s", dir_rel)
                    return None, None
                if orig_dir.is_dir():
                    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in dir_rel)
                    cache_dir = self.cache_dir / safe
                    # 源目录内容指纹比对：源有增删改即整体重拷。不能用缓存目录
                    # mtime 判断——每次加载都会写入 .py，把缓存 mtime 顶得比源新，
                    # 源目录后补的数据/模块文件将永远无法同步。
                    current_fp = self._dir_fingerprint(orig_dir)
                    fp_file = cache_dir / ".source_fingerprint"
                    needs_copy = (
                        not cache_dir.exists()
                        or not fp_file.is_file()
                        or fp_file.read_text(encoding="utf-8") != current_fp
                    )
                    if needs_copy:
                        shutil.rmtree(cache_dir, ignore_errors=True)
                        self._copy_dir_contents(orig_dir, cache_dir)
                        fp_file.write_text(current_fp, encoding="utf-8")
                    py_path = cache_dir / py_name
                    if not self._py_path_inside(cache_dir, py_path):
                        return None, None
                    py_path.write_text(code, encoding="utf-8")
                    if requirements:
                        self._merge_requirements(cache_dir, requirements)
                    return cache_dir, py_path

            # 退化路径：单文件物化
            safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in example_id)
            cache_dir = self.cache_dir / safe_id
            cache_dir.mkdir(parents=True, exist_ok=True)
            py_path = cache_dir / py_name
            if not self._py_path_inside(cache_dir, py_path):
                return None, None
            py_path.write_text(code, encoding="utf-8")
            if requirements:
                self._merge_requirements(cache_dir, requirements)
            return cache_dir, py_path
        except OSError as e:
            get_logger(__name__).error("物化 JSON 示例失败 %s: %s", example_id, e)
            return None, None

    @staticmethod
    def _py_path_inside(cache_dir: Path, py_path: Path) -> bool:
        """校验物化目标文件名不含 '..' / 绝对路径等越界成分。"""
        try:
            py_path.resolve().relative_to(cache_dir.resolve())
        except ValueError:
            get_logger(__name__).error("示例文件名越界，拒绝物化: %s", py_path)
            return False
        return True

    def _dir_fingerprint(self, directory: Path) -> str:
        """目录内容指纹：相对路径 + 大小 + mtime 的哈希，用于检测源目录增删改。"""
        import hashlib

        h = hashlib.sha256()
        for p in sorted(directory.rglob("*")):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if not p.is_file():
                continue
            st = p.stat()
            h.update(f"{p.relative_to(directory).as_posix()}|{st.st_size}|{int(st.st_mtime)}\n".encode())
        return h.hexdigest()

    def _copy_dir_contents(self, src: Path, dst: Path) -> None:
        """拷贝目录的直接子项（子目录递归拷贝），跳过缓存/版本目录。"""
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            if child.name in SKIP_DIRS:
                continue
            if child.is_dir():
                self._copy_dir_contents(child, dst / child.name)
            else:
                shutil.copy2(child, dst / child.name)

    def _merge_requirements(self, cache_dir: Path, requirements: list) -> None:
        """把 requirements 合并写入 ``cache_dir/requirements.txt``（与已有内容取并集）。

        同一缓存目录会被该目录下的多个示例共享，必须合并依赖而非相互覆盖；
        也会与原始目录拷贝过来的 requirements.txt 合并。
        非法包名（如历史迁移数据中的 UTF-16 乱码）会被丢弃，
        避免一条坏行导致整个 requirements.txt 在 pip 安装时报错。
        """
        existing: list[str] = []
        req_file = cache_dir / "requirements.txt"
        if req_file.exists():
            try:
                for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        existing.append(re.split(r"[<>=!~ ]", line, maxsplit=1)[0].strip())
            except OSError:
                pass
        merged = list(dict.fromkeys(existing + [str(r) for r in requirements]))
        merged = [r for r in merged if _VALID_PKG_RE.match(r)]
        # 总是重写（本方法仅在示例声明了 requirements 时被调用）：
        # 已有内容中的非法包名随本次合并一并清除，实现旧缓存自我修复
        req_file.write_text("\n".join(merged) + ("\n" if merged else ""), encoding="utf-8")

    def _run_pythonpath(self, dir_rel: str | None, cache_dir: Path) -> list[str]:
        """返回运行该示例时应加入 sys.path 的目录列表。

        包含：原始目录（及其所有祖先目录，向上到仓库根）用于解析包/兄弟导入；
        以及缓存目录（含物化后的同目录兄弟文件）。
        """
        paths: list[str] = [str(cache_dir)]
        if dir_rel and self._source_root is not None:
            orig_dir = self._source_root / dir_rel
            if orig_dir.is_dir():
                cur: Path | None = orig_dir
                while cur is not None:
                    paths.append(str(cur))
                    if cur == self._source_root:
                        break
                    parent = cur.parent
                    if parent == cur:
                        break
                    cur = parent
        return paths

    def _refresh_categories(self, root: ExampleItem) -> None:
        cats = set(self.DEFAULT_CATEGORIES)

        def _walk(item: ExampleItem) -> None:
            if not item.is_dir and item.category:
                cats.add(item.category)
            for child in item.children:
                _walk(child)

        _walk(root)
        self._categories = tuple(sorted(cats))

    @property
    def categories(self) -> tuple[str, ...]:
        """当前已加载示例涉及的分类（含默认三类）。"""
        return self._categories

    def ensure_quality_score(self, item: ExampleItem) -> int:
        """惰性计算示例的质量评分并缓存到 item.quality_score。

        加载时不做 AST 解析，首次需要时才计算；已计算过则直接返回缓存值。
        评分失败时返回 0，不抛出异常。
        """
        if item.quality_score is not None:
            return item.quality_score
        if item.is_dir:
            item.quality_score = 0
            return 0
        try:
            item.quality_score = self._scorer.score(item).score
        except Exception:  # noqa: BLE001 - 评分失败不应阻断使用
            item.quality_score = 0
        return item.quality_score

    def _high_risk_findings(self, item: ExampleItem, key: str, code: str, tree: ast.AST) -> list[dict]:
        """执行安全扫描并返回 HIGH 风险明细（不读缓存，供内部共享一次解析结果）。"""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # content+tree 同时传入：check 不再自行读盘，避免与内存代码分叉
                report = self._scorer.security_checker.check(Path(str(item.path)), key, content=code, tree=tree)
            return [
                {"description": r.description, "category": r.category}
                for r in report.risk_details
                if r.level == RiskLevel.HIGH
            ]
        except Exception:  # noqa: BLE001 - 安全判定失败不阻断列表加载
            return []

    def ensure_risk_findings(self, item: ExampleItem) -> list[dict]:
        """惰性判定示例的 HIGH 风险明细并缓存，供前端高危确认弹窗展示。"""
        key = str(item.json_id or item.name)
        cached = self._risk_findings.get(key)
        if cached is not None:
            return cached
        findings: list[dict] = []
        code = item.code or ""
        if not item.is_dir and code.strip():
            tree = parse_code(code)
            if tree is not None:
                findings = self._high_risk_findings(item, key, code, tree)
        self._risk_findings[key] = findings
        return findings

    def ensure_risk_high(self, item: ExampleItem) -> bool:
        """惰性判定示例是否安全高危（HIGH 风险且不在白名单），结果缓存。

        与质量评分同样惰性：首次序列化时才做一次 AST 安全扫描，
        供前端在卡片与详情页展示高危徽章。与 ensure_risk_findings 同源。
        """
        return bool(self.ensure_risk_findings(item))

    def set_module_python(self, python_exe: str | None) -> None:
        """注入共享 .venv 解释器并（重）构建模块索引，用于缺依赖判定。

        索引变化会影响判定结果，因此清空已有的 run_status 缓存。
        """
        self._module_index = ModuleIndex(python_exe)
        self._run_status.clear()

    def ensure_run_status(self, item: ExampleItem) -> str:
        """惰性判定示例可运行性状态并缓存（broken > empty > missing_deps > risky > runnable）。

        与 ensure_risk_findings 共享同一次 AST 解析与安全扫描，避免重复开销；
        模块索引不可用时跳过缺依赖维度（宁可漏报不误报）。
        """
        key = str(item.json_id or item.name)
        cached = self._run_status.get(key)
        if cached is not None:
            return cached
        code = item.code or ""
        if item.is_dir or not code.strip():
            status = EMPTY
        elif (tree := parse_code(code)) is None:
            status = BROKEN
        elif is_empty_body(tree, code):
            status = EMPTY
        else:
            findings = self._risk_findings.get(key)
            if findings is None:
                findings = self._high_risk_findings(item, key, code, tree)
                self._risk_findings[key] = findings
            if self._module_index is not None and self._module_index.available:
                mods = third_party_imports(code, tree, [Path(p) for p in item.run_pythonpath])
                if self._module_index.missing_modules(mods):
                    status = MISSING_DEPS
                else:
                    status = RISKY if findings else RUNNABLE
            else:
                status = RISKY if findings else RUNNABLE
        self._run_status[key] = status
        return status

    # ------------------------------------------------------------------ 搜索
    def search(self, query: str, root: ExampleItem | None = None) -> list[ExampleItem]:
        """根据关键词搜索示例（匹配名称、说明/README、内联代码）。"""
        if root is None:
            root = self._root
        if root is None:
            return []
        query_lower = query.lower()
        results: list[ExampleItem] = []
        self._search_recursive(root, query_lower, results)
        return results

    def _search_recursive(self, item: ExampleItem, query_lower: str, results: list[ExampleItem]) -> None:
        if not item.is_dir:
            matched = False
            # 1. 名称 / 文件名匹配
            if query_lower in item.name.lower() or query_lower in item.path.name.lower():
                results.append(item)
                matched = True
            # 2. README / 说明内容匹配
            if not matched and item.readme_path and item.readme_path.exists():
                try:
                    content = item.readme_path.read_text(encoding="utf-8", errors="ignore").lower()
                    if query_lower in content:
                        results.append(item)
                        matched = True
                except OSError:
                    pass
            # 3. 内联代码内容匹配
            if not matched and item.code and query_lower in item.code.lower():
                results.append(item)

        for child in item.children:
            self._search_recursive(child, query_lower, results)

    # --------------------------------------------------------------- 回写
    def save_item(self, item: ExampleItem, new_code: str) -> bool:
        """把最新代码写回对应的 JSON 文件（唯一真相源），并同步到缓存文件。"""
        if item.source != "json" or item.json_file is None or item.json_id is None:
            return False
        try:
            data = json.loads(item.json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            get_logger(__name__).error("读取 JSON 失败 %s: %s", item.json_file, e)
            return False

        changed = False
        for spec in data.get("examples", []):
            if isinstance(spec, dict) and spec.get("id") == item.json_id:
                spec["code"] = new_code
                changed = True
                break
        if not changed:
            return False

        try:
            # 临时文件 + 原子替换：直接原地覆盖写在中途崩溃（进程被杀/断电）时
            # 会截断整个集合文件（内含几十上百个示例），且 git 之外无副本
            tmp = item.json_file.with_name(item.json_file.name + ".tmp")
            try:
                tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(tmp, item.json_file)
            finally:
                tmp.unlink(missing_ok=True)
            # 同步写入缓存中的实际文件（item.path 已指向重建目录里的目标文件，
            # 下次加载物化时也会从 JSON 重建，截断可自愈）
            item.path.write_text(new_code, encoding="utf-8")
            item.code = new_code
            # 代码已变：安全判定、质量评分、可运行性缓存一并失效，下次序列化时重算
            self._risk_findings.pop(str(item.json_id), None)
            self._run_status.pop(str(item.json_id), None)
            item.quality_score = None
            return True
        except OSError as e:
            get_logger(__name__).error("回写 JSON 失败 %s: %s", item.json_file, e)
            return False

    def delete_user_example(self, item: ExampleItem) -> bool:
        """从用户集合 JSON 中删除该示例（原子写回），并清理其物化缓存与派生缓存。

        仅允许删除位于 user_dir 内的集合条目——内置集合受保护。
        用户示例均无 dir（单文件物化），缓存目录 cache_dir/<safe_id> 独立可整删。
        """
        if item.source != "json" or item.json_file is None or item.json_id is None:
            return False
        if not self.is_user_collection(item.json_file):
            get_logger(__name__).warning("拒绝删除非用户集合示例: %s", item.json_id)
            return False
        try:
            data = json.loads(item.json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            get_logger(__name__).error("读取用户集合失败 %s: %s", item.json_file, e)
            return False

        examples = data.get("examples", [])
        remaining = [s for s in examples if not (isinstance(s, dict) and s.get("id") == item.json_id)]
        if len(remaining) == len(examples):
            return False  # 集合里已无此条目
        data["examples"] = remaining

        try:
            if not remaining:
                # 集合已删空：整个集合文件一并移除，避免残留空 📦 节点
                item.json_file.unlink(missing_ok=True)
            else:
                # 临时文件 + 原子替换（与 save_item 同一防护：中途崩溃不截断集合文件）
                tmp = item.json_file.with_name(item.json_file.name + ".tmp")
                try:
                    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    os.replace(tmp, item.json_file)
                finally:
                    tmp.unlink(missing_ok=True)
        except OSError as e:
            get_logger(__name__).error("删除用户示例写回失败 %s: %s", item.json_file, e)
            return False

        # 清理该示例独立的物化缓存目录（下次加载不再重建）
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in item.json_id)
        cache_dir = self.cache_dir / safe_id
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
        # 失效派生缓存（质量分挂在 item 上，随对象一起废弃）
        key = str(item.json_id)
        self._risk_findings.pop(key, None)
        self._run_status.pop(key, None)
        return True
