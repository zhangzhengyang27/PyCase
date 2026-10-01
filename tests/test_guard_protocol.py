"""重设计护栏 G7：数据访问协议金标（docs/redesign-data-contract.md §5）。

金标分两层：
1. **方法表冻结**：sidecar 暴露的 RPC 方法集合与契约 §5 逐一点名——
   增删方法必须改金标，防静默漂移（新方法漏写契约/旧方法悄悄消失都变红）。
2. **逐方法契约**：
   - `list_examples` 只发索引：无 `code`、带真实文件路径与派生事实（import/theme/状态）；
   - `get_example` 按 id 取码：内容与真实文件逐字节一致（当场改盘、当场读到新内容）；
   - `search_examples` 服务端检索：返回 id + 命中原因（name/tag/description/code）；
   - `run_example` / `save_example` / 资源上传 / 删除：一律按 id 寻址，
     调用方夹带的 `path` 参数不生效；资源与运行产物落在工作区，真相源不被写。

全部在 tmp 沙箱内跑：集合根 / 用户集合 / 工作区都在 tmp_path，
不写仓库真相源（json_examples/ 与 topics/tools/projects）。
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SIDECAR_DIR = ROOT / "electron-prototype" / "sidecar"
for _p in (str(SIDECAR_DIR), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import server  # noqa: E402


def _workspace_of(example_id: str) -> Path:
    """按 id 取真实工作区目录（目录名带 slug 哈希后缀，不能按 id 直拼）。"""
    store = server._ensure_store()
    return store.workspace_of(server._index[example_id])

# 协议名表（跨语言单一来源）：electron-prototype/shared/protocol.json
PROTOCOL_JSON = ROOT / "electron-prototype" / "shared" / "protocol.json"
GOLDEN_METHODS = set(json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))["rpc_methods"])

RUN_STATUS_STATES = {"runnable", "risky", "broken", "empty", "unknown"}


class _StubVenv:
    """运行链路替身：直接用当前解释器跑示例，不创建也不查询共享 venv。"""

    def needs_prepare(self) -> bool:
        return False

    def ensure_python(self, file_path: Path) -> tuple[bool, str]:
        return True, sys.executable


class _ProtocolEnv:
    """把 sidecar 的集合根/用户集合/工作区全部换到 tmp_path。

    与 test_guard_runtime 的 _RpcEnv 同型，但夹具是**已迁移形态（v2）**的集合：
    清单只存元数据（`file` 指向真实 .py），真实文件是真相源——G7 要守的正是这套协议。
    """

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.captured: list[dict] = []

    def __enter__(self) -> "_ProtocolEnv":
        self._orig = (
            server._store,
            server._root,
            dict(server._index),
            server.APP_DIR,
            server.DATA_DIR,
            server._USER_DIR,
            server.REPO_ROOT,
        )
        for d in ("topics", "tools", "projects"):
            (self.tmp_path / d).mkdir(exist_ok=True)
        self.builtin_dir = self.tmp_path / "json_examples"
        self.builtin_dir.mkdir(exist_ok=True)
        self.user_dir = self.tmp_path / "user_examples"
        self.user_dir.mkdir(exist_ok=True)
        self.data_dir = self.tmp_path
        self.workspace_root = self.data_dir / ".json_examples_cache"

        self._write_v2_collection(
            self.builtin_dir,
            "demo",
            [
                {
                    "id": "hello",
                    "name": "hello.py",
                    "title": "打招呼",
                    "code": "print('HELLO-ID')\n",
                },
                {
                    "id": "other",
                    "name": "other.py",
                    "title": "另一个",
                    "code": "print('OTHER-ID')\n",
                },
            ],
        )
        self._write_v2_collection(
            self.user_dir,
            "mine",
            [{"id": "mine_one", "name": "mine_one.py", "title": "我的", "code": "print('MINE')\n"}],
        )

        server.APP_DIR = self.tmp_path
        server.DATA_DIR = self.data_dir
        server._USER_DIR = self.user_dir
        server.REPO_ROOT = self.tmp_path
        server._store = None
        server._root = None
        server._index.clear()
        self._patch_send = patch.object(
            server, "_send", side_effect=lambda obj: self.captured.append(obj)
        )
        self._patch_venv = patch.object(server, "_get_venv_manager", lambda: _StubVenv())
        self._patch_send.start()
        self._patch_venv.start()
        return self

    def __exit__(self, *exc) -> bool:
        self._patch_venv.stop()
        self._patch_send.stop()
        (
            server._store,
            server._root,
            _idx,
            server.APP_DIR,
            server.DATA_DIR,
            server._USER_DIR,
            server.REPO_ROOT,
        ) = self._orig
        server._index.clear()
        return False

    @staticmethod
    def _write_v2_collection(coll_dir: Path, name: str, examples: list[dict]) -> Path:
        """把夹具 code 落成真实文件，清单写成 v2（file 指向真实文件）。"""
        src = coll_dir / name
        src.mkdir(exist_ok=True)
        entries: list[dict] = []
        for ex in examples:
            spec = dict(ex)
            code = spec.pop("code")
            (src / spec["name"]).write_text(code, encoding="utf-8")
            spec["file"] = f"{name}/{spec['name']}"
            entries.append(spec)
        manifest = coll_dir / f"{name}.json"
        manifest.write_text(
            json.dumps({"schema_version": 2, "name": name, "examples": entries}, ensure_ascii=False),
            encoding="utf-8",
        )
        return manifest

    # ----------------------------------------------------------------- 断言工具
    def last_result(self) -> dict:
        for obj in reversed(self.captured):
            if "result" in obj:
                return obj["result"]
        raise AssertionError("未捕获任何 result")

    def last_error(self) -> dict:
        for obj in reversed(self.captured):
            if "error" in obj:
                return obj["error"]
        raise AssertionError("未捕获任何 error")

    def texts(self) -> list[str]:
        return [
            e["params"].get("text", "")
            for e in self.captured
            if e.get("method") == "run_output"
        ]

    def finished(self) -> list[dict]:
        return [e["params"] for e in self.captured if e.get("method") == "run_finished"]


# --------------------------------------------------------------- 金标 1：方法表


def test_g7_method_table_golden():
    """方法表冻结：与契约 §5 的点名集合逐项相等（增删都要先改契约）。"""
    assert set(server.METHODS) == GOLDEN_METHODS
    assert all(callable(h) for h in server.METHODS.values())


def test_g7_main_forwards_notifications_from_single_source():
    """主进程通知转发必须由 shared/protocol 的 NOTIFICATIONS 名表驱动。

    漂移实锤（2026-09 审计 B3/D2）：protocol.json / protocol.ts / server.py 三处
    都登记了 env_progress，唯独主进程的手写六项白名单漏了它——首启引导的阶段
    推送整条链路静默失效，smoke 因轮询式断言没抓到。金标断言主进程 import
    名表（TS↔JSON 的一致性由 protocol.spec.ts 钉），手写白名单不得回归。
    """
    src = (ROOT / "electron-prototype" / "electron" / "src" / "main" / "index.ts").read_text(encoding="utf-8")
    assert "shared/protocol" in src, "主进程必须从 shared/protocol 引入协议名表（单一来源第四副本禁令）"
    assert re.search(r"\bNOTIFICATIONS\b", src), "通知转发必须由 NOTIFICATIONS 名表驱动"
    assert not re.search(r"msg\.method === 'run_output'", src), "不得手写通知名白名单（漂移温床）"


# ------------------------------------------------------- 金标 2：列表只发索引


def test_g7_list_examples_is_index_only(tmp_path):
    """list_examples 只发索引：无 code、带真实文件路径与派生事实，树与数组同形。"""
    with _ProtocolEnv(tmp_path) as env:
        server.method_list_examples(1, {})
        result = env.last_result()
        assert result["total"] == 3, "列表覆盖内置 + 用户集合"
        by_id = {ex["id"]: ex for ex in result["examples"]}
        assert set(by_id) == {"hello", "other", "mine_one"}

        for ex in result["examples"]:
            assert "code" not in ex, "v2 列表不得夹带源码（契约 §5）"
            assert Path(ex["path"]).is_file(), "列表必须带真实文件路径"
            assert not Path(ex["path"]).is_relative_to(env.workspace_root), "路径应指向真相源而非工作区"
            assert isinstance(ex["import_tags"], list)
            assert ex["theme_key"] is None or isinstance(ex["theme_key"], str)
            assert ex["run_status"] in RUN_STATUS_STATES
            assert isinstance(ex["run_pythonpath"], list)
            assert isinstance(ex["quality_score"], int)

        def walk(node: dict) -> list[dict]:
            out = [node]
            for child in node.get("children") or []:
                out.extend(walk(child))
            return out

        assert result["tree"] is not None
        for node in walk(result["tree"]):
            if node.get("is_dir"):
                continue
            assert "code" not in node, "树节点同样不得夹带源码"


# ------------------------------------------------- 金标 3：按 id 取码 = 读真实文件


def test_g7_get_example_reads_real_file_on_demand(tmp_path):
    """get_example 的 code 必须等于真实文件内容——当场改盘、当场读到新内容。"""
    with _ProtocolEnv(tmp_path) as env:
        real_file = env.builtin_dir / "demo" / "hello.py"
        new_code = "# 外力修改\nprint('RELOADED')\n"
        real_file.write_text(new_code, encoding="utf-8")

        server.method_get_example(7, {"id": "hello"})
        item = env.last_result()
        assert item["code"] == new_code
        assert Path(item["path"]) == real_file

        server.method_get_example(8, {"id": "does-not-exist"})
        assert env.last_error()["code"] == -32602


# ------------------------------------------------------ 金标 4：服务端检索语义


def test_g7_search_examples_server_side_with_reason(tmp_path):
    """search_examples 返回 id + 命中原因；元数据命中不读盘，code 命中按需读文件。"""
    with _ProtocolEnv(tmp_path) as env:
        server.method_search_examples(1, {"query": "hello"})
        hits = {h["id"]: h["reason"] for h in env.last_result()["hits"]}
        assert hits == {"hello": "name"}

        # 只在 code 里出现的词：靠按需读真实文件命中
        server.method_search_examples(2, {"query": "OTHER-ID"})
        hits = {h["id"]: h["reason"] for h in env.last_result()["hits"]}
        assert hits == {"other": "code"}

        # 空查询不发散（前端防抖窗口内的空串不应全量返回）
        server.method_search_examples(3, {"query": "   "})
        assert env.last_result()["hits"] == []

        # limit 夹到 [1, 200]
        server.method_search_examples(4, {"query": "e", "limit": 1})
        assert len(env.last_result()["hits"]) == 1


# ------------------------------------------- 金标 5：运行按 id 寻址（path 不生效）


def test_g7_run_example_addresses_by_id_ignores_path(tmp_path):
    """run_example 只认 id：夹带 path 不得换出运行目标，且在工作区内执行。"""
    with _ProtocolEnv(tmp_path) as env:

        async def scenario() -> dict:
            await server.method_run_example(
                1,
                {"id": "hello", "args": [], "timeout": 30, "path": str(env.builtin_dir / "demo" / "other.py")},
            )
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if env.finished():
                    return env.finished()[-1]
                await asyncio.sleep(0.05)
            raise AssertionError("run_finished 未到达")

        finished = asyncio.run(scenario())
        assert finished["exit_code"] == 0
        joined = "".join(env.texts())
        assert "HELLO-ID" in joined
        assert "OTHER-ID" not in joined, "夹带 path 换掉了运行目标（契约 §5：按 id 寻址）"

        workspace = _workspace_of("hello")
        assert (workspace / "hello.py").is_file(), "运行必须经 ensure_workspace 落在工作区"


# --------------------------------------------------- 金标 6：保存写真实文件


def test_g7_save_example_writes_real_file_by_id(tmp_path):
    """save_example 按 id 写真实文件（原子）：夹带 path 不生效、清单不被回写、无 .tmp 残留。"""
    with _ProtocolEnv(tmp_path) as env:
        real_file = env.builtin_dir / "demo" / "hello.py"
        other_file = env.builtin_dir / "demo" / "other.py"
        manifest = env.builtin_dir / "demo.json"
        manifest_before = manifest.read_text(encoding="utf-8")
        other_before = other_file.read_text(encoding="utf-8")

        server.method_save_example(
            1,
            {"id": "hello", "code": "print('SAVED')\n", "path": str(other_file)},
        )
        assert env.last_result()["status"] == "saved"
        assert real_file.read_text(encoding="utf-8") == "print('SAVED')\n"
        assert other_file.read_text(encoding="utf-8") == other_before
        assert manifest.read_text(encoding="utf-8") == manifest_before, "v2 保存不得回写清单"

        leftovers = [p.name for p in real_file.parent.iterdir() if p.name != real_file.name]
        assert leftovers == ["other.py"], f"保存残留了临时文件: {leftovers}"

        async def rerun() -> None:
            # 工作区基线跟随：保存后立即再跑，必须跑新代码
            await server.method_run_example(2, {"id": "hello", "args": [], "timeout": 30})
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline and not env.finished():
                await asyncio.sleep(0.05)
            assert env.finished(), "run_finished 未到达"

        asyncio.run(rerun())
        assert "SAVED" in "".join(env.texts())


# --------------------------------------- 金标 7：资源落工作区，不写真相源


def test_g7_asset_upload_lands_in_workspace(tmp_path):
    """上传资源 = 工作区内的文件：真相源目录不被写，运行目录里能看到它。"""
    with _ProtocolEnv(tmp_path) as env:
        import base64

        payload = base64.b64encode(b"\x89PNG\r\n").decode("ascii")
        server.method_upload_asset(1, {"id": "hello", "filename": "pic.png", "data": payload})
        result = env.last_result()
        target = Path(result["path"])
        assert target.is_file()
        assert target.is_relative_to(env.workspace_root)
        assert not target.is_relative_to(env.builtin_dir), "资源不得写进真相源目录"

        server.method_list_assets(2, {"id": "hello"})
        names = [a["filename"] for a in env.last_result()["assets"]]
        assert "pic.png" in names
        assert "hello.py" not in names, "脚本本体不算资源（受保护名单）"

        server.method_delete_asset(3, {"id": "hello", "filename": "pic.png"})
        assert env.last_result()["deleted"] == "pic.png"
        assert not target.exists()


# --------------------------------- 金标 8：用户示例删除 = 清单 + 文件 + 工作区三处


def test_g7_delete_user_example_cleans_three_places(tmp_path):
    """删除用户示例：清单条目、真实文件、工作区三处同步清理；内置集合受保护。"""
    with _ProtocolEnv(tmp_path) as env:
        server.method_upload_asset(
            1,
            {
                "id": "mine_one",
                "filename": "asset.txt",
                "data": "aGVsbG8=",  # "hello"
            },
        )
        real_file = env.user_dir / "mine" / "mine_one.py"
        workspace = _workspace_of("mine_one")
        assert real_file.is_file() and workspace.is_dir()

        server.method_delete_example(2, {"id": "mine_one"})
        assert env.last_result()["deleted"] == "mine_one"
        assert not real_file.exists(), "真实文件未随删除清理"
        assert not workspace.exists(), "工作区未随删除清理"
        assert (env.user_dir / "mine.json").exists() is False or json.loads(
            (env.user_dir / "mine.json").read_text(encoding="utf-8")
        )["examples"] == []

        server.method_delete_example(3, {"id": "hello"})
        assert env.last_error()["code"] == -32602
        assert (env.builtin_dir / "demo" / "hello.py").is_file()


# ------------------------------------------------- 金标 9：内置数据仍不带 code


def test_g7_builtin_dataset_listing_carries_no_code():
    """真内置数据的列表响应不含任何 code（v1 兼容期也必须走"只发索引"的协议）。"""
    captured: list[dict] = []
    orig = (server._store, server._root, dict(server._index))
    server._store = None
    server._root = None
    server._index.clear()
    try:
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            server.method_list_examples(1, {})
    finally:
        server._store, server._root, saved_index = orig
        server._index.clear()
        server._index.update(saved_index)

    result = next(obj["result"] for obj in captured if "result" in obj)
    assert result["total"] == 1496
    assert all("code" not in ex for ex in result["examples"])
    assert all(Path(ex["path"]).exists() for ex in result["examples"])
