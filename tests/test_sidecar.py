"""sidecar 模块单元测试：argparse 静态解析、JSON-RPC 协议、环境变量白名单。

无需启动 Electron 或真实子进程，直接导入 sidecar.server 的纯函数进行测试。
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# sidecar 位于 electron-prototype/sidecar/，需要加入 sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
SIDECAR_DIR = ROOT / "electron-prototype" / "sidecar"
sys.path.insert(0, str(SIDECAR_DIR))
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def _make_v2_store(tmp_path: Path, examples: list[dict], collection: str = "demo"):
    """v2 夹具：把 code 落成真实文件并写 file 字段（契约 §2.2），返回 (store, index)。

    ``_ensure_store()`` 会加载真实库（1496 条，慢），资源/风险用例必须注入假 store，
    且工作区根落在 tmp_path 下，任何落盘都不碰真实数据。
    注：无 code 且无 file 的条目没有内容来源，load 期应被跳过——保留在夹具里断言该行为。
    """
    coll = tmp_path / "json_examples"
    coll.mkdir(exist_ok=True)
    src_dir = coll / collection
    src_dir.mkdir(exist_ok=True)
    entries: list[dict] = []
    for ex in examples:
        spec = dict(ex)
        code = spec.pop("code", None)
        if code is not None:
            (src_dir / spec["name"]).write_text(code, encoding="utf-8")
            spec["file"] = f"{collection}/{spec['name']}"
        entries.append(spec)
    (coll / f"{collection}.json").write_text(
        json.dumps({"schema_version": 2, "name": collection, "examples": entries}), encoding="utf-8"
    )
    store = server.ContractStore.for_base_dir(base_dir=tmp_path)
    store.load()
    return store, store.index


# ---------------------------------------------------------------------------
# argparse 静态解析测试
# ---------------------------------------------------------------------------
class TestArgparseParsing:
    def test_basic_positional(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file")
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 1
        assert specs[0]["name"] == "input"
        assert specs[0]["is_positional"] is True
        assert specs[0]["dest"] == "input"
        assert specs[0]["type"] == "str"
        assert specs[0]["help"] == "input file"

    def test_optional_with_flags(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", help="output file", default="out.txt")
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 1
        assert specs[0]["flags"] == ["-o", "--output"]
        assert specs[0]["dest"] == "output"
        assert specs[0]["default"] == "out.txt"
        assert specs[0]["is_positional"] is False

    def test_store_true_action(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", action="store_true", help="verbose output")
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 1
        assert specs[0]["action"] == "store_true"
        assert specs[0]["type"] == "bool"
        assert specs[0]["default"] is False

    def test_store_false_action(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--no-color", action="store_false", help="disable color")
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 1
        assert specs[0]["action"] == "store_false"
        assert specs[0]["type"] == "bool"
        assert specs[0]["default"] is True

    def test_int_type_with_choices(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--level", type=int, choices=[1, 2, 3], default=1)
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 1
        assert specs[0]["type"] == "int"
        assert specs[0]["choices"] == [1, 2, 3]
        assert specs[0]["default"] == 1

    def test_float_type(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--threshold", type=float, default=0.5)
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert specs[0]["type"] == "float"
        assert specs[0]["default"] == 0.5

    def test_required_flag(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--api-key", required=True, help="API key")
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert specs[0]["required"] is True

    def test_multiple_arguments(self):
        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--format", choices=["json", "csv", "xml"], default="json")
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 4
        assert specs[0]["is_positional"] is True
        assert specs[1]["is_positional"] is True
        assert specs[2]["choices"] == ["json", "csv", "xml"]
        assert specs[3]["action"] == "store_true"

    def test_dynamic_default_value(self):
        """默认值为动态表达式（如 os.environ.get）时静态解析应安全回退为 None。

        Python 3.14 已移除 ast.Num/Str/NameConstant 兼容别名，
        兼容层代码在非 Constant 节点上不得抛 AttributeError。
        """
        code = """
import argparse
import os
parser = argparse.ArgumentParser()
parser.add_argument("--name", default=os.environ.get("USER_NAME"))
args = parser.parse_args()
"""
        specs = server._parse_argparse_from_code(code)
        assert len(specs) == 1
        assert specs[0]["default"] is None

    def test_syntax_error_returns_empty(self):
        code = "this is not valid python !!!"
        specs = server._parse_argparse_from_code(code)
        assert specs == []

    def test_no_argparse_returns_empty(self):
        code = "print('hello world')"
        specs = server._parse_argparse_from_code(code)
        assert specs == []


# ---------------------------------------------------------------------------
# 环境变量白名单测试
# ---------------------------------------------------------------------------
class TestSafeEnv:
    def test_whitelist_filters_sensitive_vars(self):
        with patch.dict(
            os.environ,
            {
                "PATH": "/usr/bin",
                "HOME": "/home/user",
                "API_KEY": "secret-key-123",
                "AWS_SECRET_ACCESS_KEY": "aws-secret",
                "DATABASE_PASSWORD": "db-pass",
                "PYTHONPATH": "/extra/path",
            },
            clear=True,
        ):
            env = server._build_safe_env()
            assert "PATH" in env
            assert "HOME" in env
            assert "PYTHONPATH" in env
            assert "API_KEY" not in env
            assert "AWS_SECRET_ACCESS_KEY" not in env
            assert "DATABASE_PASSWORD" not in env

    def test_extra_vars_are_injected(self):
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            env = server._build_safe_env({"CUSTOM_VAR": "value", "PYTHONUNBUFFERED": "1"})
            assert env["CUSTOM_VAR"] == "value"
            assert env["PYTHONUNBUFFERED"] == "1"
            assert env["PATH"] == "/usr/bin"

    def test_extra_overrides_whitelist(self):
        with patch.dict(os.environ, {"PATH": "/original"}, clear=True):
            env = server._build_safe_env({"PATH": "/override"})
            assert env["PATH"] == "/override"


# ---------------------------------------------------------------------------
# JSON-RPC 协议处理测试
# ---------------------------------------------------------------------------
class TestJsonRpcProtocol:
    def test_invalid_json_returns_parse_error(self):
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            asyncio.run(server._handle_request("not valid json {{{"))
        assert len(captured) == 1
        assert captured[0]["error"]["code"] == -32700

    def test_invalid_jsonrpc_version_returns_invalid_request(self):
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            asyncio.run(server._handle_request(json.dumps({"jsonrpc": "1.0", "id": 1, "method": "ping"})))
        assert len(captured) == 1
        assert captured[0]["error"]["code"] == -32600

    def test_non_dict_request_returns_invalid_request(self):
        """合法 JSON 但非对象（数组/字符串/数字/null）应返回 -32600 而非让进程崩溃。"""
        for payload in ("[1,2,3]", '"abc"', "123", "null"):
            captured = []
            with patch.object(server, "_send", side_effect=lambda obj, sink=captured: sink.append(obj)):
                asyncio.run(server._handle_request(payload))
            assert len(captured) == 1, payload
            assert captured[0]["error"]["code"] == -32600, payload

    def test_unknown_method_returns_method_not_found(self):
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            asyncio.run(
                server._handle_request(json.dumps({"jsonrpc": "2.0", "id": 42, "method": "nonexistent_method"}))
            )
        assert len(captured) == 1
        assert captured[0]["error"]["code"] == -32601
        assert captured[0]["id"] == 42

    def test_ping_returns_ok(self):
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            asyncio.run(server._handle_request(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})))
        assert len(captured) == 1
        assert captured[0]["id"] == 1
        assert captured[0]["result"]["status"] == "ok"
        assert "python" in captured[0]["result"]

    def test_empty_line_is_ignored(self):
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            asyncio.run(server._handle_request("   \n  "))
        assert len(captured) == 0

    def test_notification_format(self):
        """验证 _notify 生成的消息没有 id 字段（JSON-RPC 通知规范）。"""
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            server._notify("run_output", {"run_id": "abc", "text": "hello"})
        assert len(captured) == 1
        assert "id" not in captured[0]
        assert captured[0]["jsonrpc"] == "2.0"
        assert captured[0]["method"] == "run_output"
        assert captured[0]["params"]["run_id"] == "abc"


# ---------------------------------------------------------------------------
# 图片收集测试
# ---------------------------------------------------------------------------
class TestCollectImages:
    def test_collects_recent_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # 创建一个"老"图片（mtime 设为 10 秒前）
            old_img = tmp / "old.png"
            old_img.write_bytes(b"\x89PNG\r\n\x1a\n")
            import time

            old_time = time.time() - 10
            os.utime(old_img, (old_time, old_time))

            # 创建一个"新"图片
            new_img = tmp / "new.png"
            new_img.write_bytes(b"\x89PNG\r\n\x1a\n")

            since = time.time() - 2
            images = server._collect_images(tmp, since)
            # 新图片应该被收集，老图片不应该
            assert any("new.png" in u for u in images)
            assert not any("old.png" in u for u in images)

    def test_non_image_files_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "data.txt").write_text("not an image")
            (tmp / "script.py").write_text("print('hi')")
            (tmp / "result.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            import time

            images = server._collect_images(tmp, time.time() - 1)
            assert len(images) == 1
            assert "result.png" in images[0]

    def test_recursive_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            sub = tmp / "files" / "output"
            sub.mkdir(parents=True)
            (sub / "deep_result.jpg").write_bytes(b"\xff\xd8\xff")
            import time

            images = server._collect_images(tmp, time.time() - 1)
            assert any("deep_result.jpg" in u for u in images)

    def test_limit_max_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            for i in range(20):
                (tmp / f"img_{i:02d}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            import time

            images = server._collect_images(tmp, time.time() - 1)
            assert len(images) <= 12  # 默认 limit=12


# ---------------------------------------------------------------------------
# 资源上传保护测试
# ---------------------------------------------------------------------------
class TestEnvStatus:
    """环境状态协议（A5.5）：首启页与帮助面板消费，字段必须是可核对的真实值。"""

    def test_snapshot_reports_facts(self):
        snap = server._env_snapshot()
        assert set(["phase", "started_at", "error", "log_path", "mode", "venv_path", "venv_ready", "python_version"]).issubset(snap)
        assert snap["mode"] == "shared"
        assert snap["phase"] in ("starting", "preparing", "indexing", "warming", "ready", "failed")
        # 版本串取自当前解释器，不是写死的
        assert snap["python_version"] == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def test_set_run_env_validates_mode(self):
        sent = []
        with patch.object(server, "_result", lambda rid, res: sent.append(res)):
            server.method_set_run_env("1", {"mode": "system"})
        assert server._run_env_mode == "system"
        assert sent and sent[-1]["mode"] == "system"

        errs = []
        with patch.object(server, "_error", lambda rid, code, msg: errs.append((code, msg))):
            server.method_set_run_env("2", {"mode": "wat"})
        assert errs and errs[-1][0] == -32602
        assert server._run_env_mode == "system"  # 非法值不改状态

    def test_phase_transition_broadcasts_and_keeps_error(self):
        events = []
        with patch.object(server, "_notify", lambda m, p: events.append((m, p))):
            server._set_env_phase("failed", "pip 安装超时")
        assert events and events[-1][0] == "env_progress"
        assert events[-1][1]["phase"] == "failed"
        assert events[-1][1]["error"] == "pip 安装超时"
        # 还原，避免影响其它用例
        server._env_state["phase"] = "starting"
        server._env_state["error"] = ""
        server._run_env_mode = "shared"


class TestCollectAssets:
    """资源面板列出的是工作区里的**用户资产**：受保护文件（示例脚本 / requirements.txt）
    与工作区账本 .manifest.json 不得混入——它们删不掉或属内部数据，列出来只会给出
    "能删但删不掉"的死入口（A4 走查发现；契约 §4.2/§5）。"""

    def _item(self, tmp_path: Path):
        store, index = _make_v2_store(tmp_path, [{"id": "demo1", "name": "demo.py", "code": "print('hi')\n"}])
        return store, index["demo1"]

    def test_protected_files_not_listed(self, tmp_path):
        store, item = self._item(tmp_path)
        with patch.object(server, "_store", store):
            workspace = server._asset_dir(item)  # v2：资源目录 = 工作区（先经 ensure_workspace）
            assert (workspace / "demo.py").is_file()  # 脚本基线随工作区到位
            (workspace / "requirements.txt").write_text("requests\n", encoding="utf-8")
            (workspace / "data.csv").write_text("a,b\n", encoding="utf-8")
            assets = server._collect_assets(item)
        names = [a["filename"] for a in assets]
        assert names == ["data.csv"]

    def test_image_flag_and_size(self, tmp_path):
        store, item = self._item(tmp_path)
        with patch.object(server, "_store", store):
            workspace = server._asset_dir(item)
            (workspace / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            assets = server._collect_assets(item)
        assert len(assets) == 1
        assert assets[0]["filename"] == "shot.png"
        assert assets[0]["is_image"] is True
        assert assets[0]["size"] == 8


class TestUploadAssetGuard:
    def _make_item(self, tmp_path: Path):
        """构造一个 v2 形态的 json 示例（真实文件 + file 字段）及其索引项。"""
        store, index = _make_v2_store(tmp_path, [{"id": "demo1", "name": "demo1.py", "code": "print('x')"}])
        item = index["demo1"]
        store_orig = server._store
        root_orig = server._root
        index_orig = dict(server._index)
        server._store = store
        server._root = store.root
        server._index.clear()
        server._index[item.json_id] = item
        return item, store_orig, root_orig, index_orig

    def _restore(self, store_orig, root_orig, index_orig):
        server._store = store_orig
        server._root = root_orig
        server._index.clear()
        server._index.update(index_orig)

    def test_upload_cannot_overwrite_script(self, tmp_path):
        item, s0, r0, i0 = self._make_item(tmp_path)
        try:
            script = item.path  # v2：item.path 就是真实文件
            original = script.read_text(encoding="utf-8")
            captured = []
            with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
                server.method_upload_asset(1, {"id": item.json_id, "filename": "demo1.py", "data": "aGk="})
            assert "error" in captured[0], "上传同名 .py 必须被拒绝（所见非所跑）"
            assert script.read_text(encoding="utf-8") == original
        finally:
            self._restore(s0, r0, i0)

    def test_upload_cannot_overwrite_requirements(self, tmp_path):
        item, s0, r0, i0 = self._make_item(tmp_path)
        try:
            captured = []
            with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
                server.method_upload_asset(1, {"id": item.json_id, "filename": "requirements.txt", "data": "aGk="})
            assert "error" in captured[0], "上传 requirements.txt 必须被拒绝（任意装包）"
            assert not (server._asset_dir(item) / "requirements.txt").exists()
        finally:
            self._restore(s0, r0, i0)

    def test_upload_normal_file_still_works(self, tmp_path):
        item, s0, r0, i0 = self._make_item(tmp_path)
        try:
            captured = []
            with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
                server.method_upload_asset(1, {"id": item.json_id, "filename": "photo.png", "data": "aGk="})
            assert "result" in captured[0]
            # v2：资源落在运行工作区（契约 §4.1/§5），真实源码树不被污染
            workspace = server._asset_dir(item)
            assert (workspace / "photo.png").is_file()
            assert not (item.path.parent / "photo.png").exists()
        finally:
            self._restore(s0, r0, i0)

    def test_delete_cannot_remove_script(self, tmp_path):
        item, s0, r0, i0 = self._make_item(tmp_path)
        try:
            script = item.path
            captured = []
            with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
                server.method_delete_asset(1, {"id": item.json_id, "filename": "demo1.py"})
            assert "error" in captured[0], "删除示例脚本必须被拒绝"
            assert script.is_file()
            assert (server._asset_dir(item) / "demo1.py").is_file()  # 工作区副本同样完好
        finally:
            self._restore(s0, r0, i0)


# ---------------------------------------------------------------------------
# stop_run 竞态修复测试
# ---------------------------------------------------------------------------
class TestStopRunRace:
    def test_stop_before_start_marks_pending(self):
        """在进程启动前调用 stop_run，应标记为 pending_terminate 而非报错。"""
        run_id = "test_pending_123"
        server._running[run_id] = None  # 模拟启动中状态
        captured = []
        try:
            with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
                asyncio.run(server.method_stop_run(1, {"run_id": run_id}))
            assert len(captured) == 1
            assert captured[0]["result"]["status"] == "pending_terminate"
            assert run_id in server._pending_stop
        finally:
            server._running.pop(run_id, None)
            server._pending_stop.discard(run_id)

    def test_stop_unknown_run_returns_error(self):
        captured = []
        with patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)):
            asyncio.run(server.method_stop_run(1, {"run_id": "nonexistent_run"}))
        assert len(captured) == 1
        assert "error" in captured[0]
        assert captured[0]["error"]["code"] == -32602

class TestRiskHigh:
    """ensure_risk_high：安全高危判定、缓存命中与保存后失效（v2：判定读真实文件）。"""

    def _make_store(self, tmp_path: Path):
        store, _index = _make_v2_store(
            tmp_path,
            [
                {"id": "safe1", "name": "safe1.py", "code": "print('hello')"},
                {"id": "risky1", "name": "risky1.py", "code": "import os\nos.system('echo hi')"},
                # 无 file 也无内联 code：没有内容来源，load 期即被跳过
                {"id": "empty1", "name": "__init__.py"},
            ],
        )
        root = store.root
        items: dict = {}

        def walk(node):
            if node.is_dir:
                if node.name != "root":
                    items.setdefault(node.name, node)
                for c in node.children:
                    walk(c)
            else:
                items[node.name] = node

        walk(root)
        return store, items, root

    def test_risk_classification(self, tmp_path):
        store, items, root = self._make_store(tmp_path)
        assert store.ensure_risk_high(items["safe1.py"]) is False
        assert store.ensure_risk_high(items["risky1.py"]) is True
        # 无内容来源的条目在 load 阶段即被跳过，不会进入示例树
        assert "__init__.py" not in items
        assert store.ensure_risk_high(root.children[0]) is False  # 目录节点恒安全

    def test_cache_invalidated_on_save(self, tmp_path):
        store, items, _root = self._make_store(tmp_path)
        item = items["risky1.py"]
        assert store.ensure_risk_high(item) is True
        assert store.save_item(item, "print('now safe')") is True
        # v2：保存写真实文件（真相源），工作区仍由 ensure_workspace 自愈
        assert item.path.read_text(encoding="utf-8") == "print('now safe')"
        # 保存后高危缓存失效：删除 os.system 后不再判高危
        assert store.ensure_risk_high(item) is False
        # 质量分缓存同样失效，等待惰性重算
        assert item.quality_score is None

class TestUserCollectionRpc:
    """scan_import_source / import_examples / delete_example（用户集合解耦链路）。

    全局 APP_DIR/DATA_DIR/_USER_DIR 全部 patch 到 tmp_path：任何写盘都落在临时目录。
    """

    def _swap(self, tmp_path):
        orig = (server._store, server._root, dict(server._index), server.APP_DIR, server.DATA_DIR, server._USER_DIR)
        coll = tmp_path / "json_examples"
        coll.mkdir()
        (coll / "builtin.json").write_text(
            json.dumps({"name": "builtin", "examples": [{"id": "b1", "name": "b1.py", "code": "print(1)\n"}]}),
            encoding="utf-8",
        )
        user_dir = tmp_path / "user_examples"
        user_dir.mkdir()
        server.APP_DIR = tmp_path
        server.DATA_DIR = tmp_path
        server._USER_DIR = user_dir
        server._store = None
        server._root = None
        server._index.clear()
        return orig

    def _restore(self, orig):
        server._store, server._root, idx, server.APP_DIR, server.DATA_DIR, server._USER_DIR = orig
        server._index.clear()
        server._index.update(idx)

    def _capture(self):
        captured = []
        return patch.object(server, "_send", side_effect=lambda obj: captured.append(obj)), captured

    def _first(self, captured):
        return captured[0]

    def test_scan_previews_without_writing(self, tmp_path):
        orig = self._swap(tmp_path)
        try:
            src = tmp_path / "src"
            src.mkdir()
            (src / "hello.py").write_text('import cv2\nprint("hi")\n', encoding="utf-8")
            (src / "empty.py").write_text("", encoding="utf-8")
            ctx, captured = self._capture()
            with ctx:
                server.method_scan_import_source(1, {"source_path": str(src)})
            resp = self._first(captured)
            assert "result" in resp
            result = resp["result"]
            assert result["total"] == 2 and len(result["files"]) == 1 and len(result["skipped"]) == 1
            assert result["files"][0]["id"] == "hello.py"
            # 预览不写盘
            assert list((server._USER_DIR).glob("*.json")) == []
        finally:
            self._restore(orig)

    def test_import_writes_collection_and_reloads_index(self, tmp_path):
        orig = self._swap(tmp_path)
        try:
            src = tmp_path / "src"
            src.mkdir()
            (src / "hello.py").write_text('import cv2\nprint("hi")\n', encoding="utf-8")
            ctx, captured = self._capture()
            with ctx:
                server.method_import_examples(1, {"source_path": str(src), "name": "我的集合"})
            result = self._first(captured)["result"]
            assert result["imported"] == 1 and result["collection"] == "user_collection"
            # 集合 JSON 落盘（中文 slug 回退 user_collection）
            files = list(server._USER_DIR.glob("*.json"))
            assert [f.stem for f in files] == ["user_collection"]
            # 索引已重建：新示例可见且带 user_collection 标记
            assert "hello.py" in server._index
            item = server._index["hello.py"]
            assert server._store.is_user_collection(item.json_file) is True
            # 集合名冲突：再导入同名单独成文件，不覆盖
            ctx, captured = self._capture()
            with ctx:
                server.method_import_examples(2, {"source_path": str(src), "name": "我的集合"})
            assert self._first(captured)["result"]["collection"] == "user_collection_2"
            assert len(list(server._USER_DIR.glob("*.json"))) == 2
        finally:
            self._restore(orig)

    def test_delete_protects_builtin_and_removes_user_example(self, tmp_path):
        orig = self._swap(tmp_path)
        try:
            # 先导入一个用户示例
            src = tmp_path / "src"
            src.mkdir()
            (src / "mine.py").write_text("print(9)\n", encoding="utf-8")
            ctx, captured = self._capture()
            with ctx:
                server.method_import_examples(1, {"source_path": str(src), "name": "mine"})
            assert "mine.py" in server._index
            # 内置示例拒绝删除
            ctx, captured = self._capture()
            with ctx:
                server.method_delete_example(2, {"id": "b1"})
            resp = self._first(captured)
            assert "error" in resp and "用户集合" in resp["error"]["message"]
            assert "b1" in server._index
            # 用户示例删除成功：索引与集合 JSON 同步
            ctx, captured = self._capture()
            with ctx:
                server.method_delete_example(3, {"id": "mine.py"})
            resp = self._first(captured)
            assert "result" in resp and resp["result"]["deleted"] == "mine.py"
            assert "mine.py" not in server._index
            # 集合删空后整个集合文件移除（不残留空 📦 节点）
            assert list(server._USER_DIR.glob("*.json")) == []
        finally:
            self._restore(orig)
