"""重设计护栏测试 G4–G6：运行链路 / 进程生命周期 / 用户集合。

- G4 运行链路：成功且输出流式实时送达、超时强杀、停止（SIGTERM）、启动前停止竞态
- G5 生命周期：示例进程留在 sidecar 进程组内（按组清理的前提）；sidecar 收到 SIGTERM
  后示例必须随之退出（当前无信号处理，示例成孤儿 → xfail 待 B2）
- G6 用户集合：重复导入 id 全局去重、导入写盘中途失败不留半成品、无可导入文件不落盘

运行链路用真解释器跑真进程；解释器注入替换为当前解释器（不触碰共享 venv）。
脚本与数据全部落在 tmp_path，不写仓库真相源与真实用户集合。
"""

import asyncio
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
SIDECAR_DIR = ROOT / "electron-prototype" / "sidecar"
for _p in (str(SIDECAR_DIR), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import server  # noqa: E402
from app.models import ExampleItem  # noqa: E402

REPO_CACHE = ROOT / ".json_examples_cache"
B2_TARGET = "B2 目标行为：旧实现尚未满足；一旦 XPASS 即表示已落地，应摘除 xfail 标记"
DRILL_CACHE_NAME = "drill_sleep"  # 演练示例 id 对应的物化目录名（与 slugify 口径一致）


# --------------------------------------------------------------------- 公共工具


class _Capture:
    """捕获 sidecar 通知（替代真实 stdout 写入）。"""

    def __init__(self) -> None:
        self.events: list[tuple[float, dict]] = []

    def __call__(self, obj: dict) -> None:
        self.events.append((time.monotonic(), obj))

    def texts(self) -> list[str]:
        return [
            e["params"].get("text", "")
            for _, e in self.events
            if e.get("method") == "run_output"
        ]

    def finished(self) -> list[dict]:
        return [
            e["params"] for _, e in self.events if e.get("method") == "run_finished"
        ]

    def time_of(self, needle: str) -> float:
        for ts, e in self.events:
            if e.get("method") == "run_output" and needle in e["params"].get(
                "text", ""
            ):
                return ts
        raise AssertionError(f"未捕获含 {needle!r} 的输出")


class _StubVenv:
    """运行链路替身：直接用当前解释器跑示例，不创建也不查询共享 venv。"""

    def needs_prepare(self) -> bool:
        return False

    def ensure_python(self, file_path: Path) -> tuple[bool, str]:
        return True, sys.executable


def _capture(monkeypatch) -> _Capture:
    cap = _Capture()
    monkeypatch.setattr(server, "_send", cap)
    monkeypatch.setattr(server, "_get_venv_manager", lambda: _StubVenv())
    return cap


def _fake_item(tmp_path: Path, code: str, name: str = "demo.py") -> ExampleItem:
    path = tmp_path / name
    path.write_text(code, encoding="utf-8")
    return ExampleItem(
        name=name,
        path=path,
        is_dir=False,
        category="user",
        source="json",
        code=code,
        json_id=name,
    )


def _pid_script(pid_file: Path, seconds: int = 120) -> str:
    return (
        "import os\n"
        "import pathlib\n"
        "import time\n"
        f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid()), encoding='utf-8')\n"
        f"time.sleep({seconds})\n"
    )


async def _wait_pid_file(pid_file: Path, timeout: float = 15.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            text = pid_file.read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        if text:
            return int(text)
        await asyncio.sleep(0.05)
    raise AssertionError(f"等待示例写出 PID 超时: {pid_file}")


def _pid_gone(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(0.05)
    return False


def _kill_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


# ------------------------------------------------------------- G4 运行链路


def test_g4_streams_output_and_reports_success(tmp_path, monkeypatch):
    """输出必须流式送达：首行在进程结束前到达，而不是攒到结束一次性吐。"""
    cap = _capture(monkeypatch)
    item = _fake_item(
        tmp_path,
        "import time\nprint('one', flush=True)\ntime.sleep(1.5)\nprint('two', flush=True)\n",
    )

    asyncio.run(server._run_subprocess("g4-ok", item, [], 30))

    texts = cap.texts()
    assert any("one" in t for t in texts) and any("two" in t for t in texts)
    finished = cap.finished()
    assert len(finished) == 1 and finished[0]["exit_code"] == 0
    finished_at = cap.events[-1][0]
    assert (
        cap.time_of("one") < finished_at - 0.5
    ), "首行输出晚于进程结束，说明输出被缓冲而非流式"


def test_g4_timeout_kills_process_hard(tmp_path, monkeypatch):
    """超时必须强制杀死进程（SIGKILL），退出码 -9，且进程真的消失。"""
    cap = _capture(monkeypatch)
    pid_file = tmp_path / "pid.txt"
    item = _fake_item(tmp_path, _pid_script(pid_file))

    asyncio.run(server._run_subprocess("g4-timeout", item, [], 1))

    assert any("超过 1 秒" in t for t in cap.texts())
    assert [f["exit_code"] for f in cap.finished()] == [-9]
    pid = int(pid_file.read_text(encoding="utf-8").strip())
    try:
        assert _pid_gone(pid), f"超时后示例进程 {pid} 仍存活"
    finally:
        _kill_pid(pid)


def test_g4_stop_terminates_running_process(tmp_path, monkeypatch):
    """停止运行：SIGTERM 终止进程，退出码 -15，前端拿到 run_finished 收尾。"""
    cap = _capture(monkeypatch)
    pid_file = tmp_path / "pid.txt"
    item = _fake_item(tmp_path, _pid_script(pid_file))
    captured_resp: list[dict] = []
    monkeypatch.setattr(
        server, "_result", lambda req_id, result: captured_resp.append(result)
    )

    async def scenario() -> int:
        task = asyncio.create_task(server._run_subprocess("g4-stop", item, [], 30))
        pid = await _wait_pid_file(pid_file)
        await server.method_stop_run(7, {"run_id": "g4-stop"})
        await asyncio.wait_for(task, timeout=15)
        return pid

    pid = asyncio.run(scenario())
    try:
        assert captured_resp and captured_resp[0]["status"] == "terminating"
        assert [f["exit_code"] for f in cap.finished()] == [-15]
        assert _pid_gone(pid), f"停止后示例进程 {pid} 仍存活"
    finally:
        _kill_pid(pid)


def test_g4_stop_before_spawn_terminates_immediately(tmp_path, monkeypatch):
    """竞态：停止请求先于子进程 spawn 到达时，启动后必须立即终止并照常收尾。"""
    cap = _capture(monkeypatch)
    item = _fake_item(tmp_path, "print('never', flush=True)\n")
    run_id = "g4-pending"
    server._running[run_id] = None
    server._pending_stop.add(run_id)
    try:
        asyncio.run(server._run_subprocess(run_id, item, [], 30))
    finally:
        server._pending_stop.discard(run_id)
        server._running.pop(run_id, None)

    assert any("已在启动前收到停止指令" in t for t in cap.texts())
    assert [f["exit_code"] for f in cap.finished()] == [-15]
    assert "never" not in "".join(cap.texts())


# ------------------------------------------------------------- G5 生命周期


def test_g5_example_stays_in_sidecar_process_group(tmp_path, monkeypatch):
    """示例进程必须留在 sidecar 进程组内——应用退出时"按组清理"才可能不漏杀。"""
    _capture(monkeypatch)
    pid_file = tmp_path / "pid.txt"
    item = _fake_item(tmp_path, _pid_script(pid_file))
    monkeypatch.setattr(server, "_result", lambda req_id, result: None)

    async def scenario() -> tuple[int, int]:
        task = asyncio.create_task(server._run_subprocess("g5-pgid", item, [], 30))
        pid = await _wait_pid_file(pid_file)
        pgid = os.getpgid(pid)
        await server.method_stop_run(1, {"run_id": "g5-pgid"})
        await asyncio.wait_for(task, timeout=15)
        return pid, pgid

    pid, pgid = asyncio.run(scenario())
    try:
        assert pgid == os.getpgid(0)
    finally:
        _kill_pid(pid)


def _drill_data_dir(tmp_path: Path, pid_file: Path) -> Path:
    """构造演练用可写数据根：用户集合 + 软链缓存 + 假共享 venv。"""
    data = tmp_path / "data"
    user = data / "user_examples"
    user.mkdir(parents=True)
    (user / "drill.json").write_text(
        json.dumps(
            {
                "name": "drill",
                "examples": [
                    {
                        "id": DRILL_CACHE_NAME,
                        "name": "drill_sleep.py",
                        "code": _pid_script(pid_file),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    # 物化缓存软链到仓库已有缓存（与生产同源）：避免冷启动重物化 1496 条
    (data / ".json_examples_cache").symlink_to(REPO_CACHE)
    # 假共享 venv：命中"已就绪"分支，不起真实创建/安装
    venv_dir = data / ".venv"
    (venv_dir / "bin").mkdir(parents=True)
    (venv_dir / "bin" / "python").symlink_to(sys.executable)
    (venv_dir / server.VenvManager.MARKER_FILE_NAME).write_text(
        '{"bootstrap": true}', encoding="utf-8"
    )
    return data


def _cleanup_drill_cache() -> None:
    """只清理本测试自己物化出来的目录（路径护栏：父目录必须是缓存根）。"""
    target = REPO_CACHE / DRILL_CACHE_NAME
    if target.parent.name != REPO_CACHE.name or target.name != DRILL_CACHE_NAME:
        return
    shutil.rmtree(target, ignore_errors=True)


def _read_line_with_timeout(stream, timeout: float) -> str:
    box: list[str] = []

    def reader() -> None:
        box.append(stream.readline())

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    t.join(timeout)
    return box[0] if box else ""


@pytest.mark.xfail(strict=True, reason=B2_TARGET)
def test_g5_sidecar_sigterm_leaves_no_orphan(tmp_path):
    """应用退出（sidecar 收到 SIGTERM）后，运行中的示例进程必须随之消失。

    今天 sidecar 没有任何信号/atexit 处理，SIGTERM 直接终止它，示例成为孤儿。
    （"按组清理"的应用侧路径由 test_g5_example_stays_in_sidecar_process_group 守住。）
    """
    pid_file = tmp_path / "example.pid"
    data_dir = _drill_data_dir(tmp_path, pid_file)
    env = dict(os.environ)
    env["DESKTOP_APP_DATA_DIR"] = str(data_dir)
    proc = subprocess.Popen(
        [sys.executable, str(SIDECAR_DIR / "server.py")],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        env=env,
    )
    example_pid: int | None = None
    try:
        assert proc.stdout is not None and proc.stdin is not None
        assert '"sidecar_ready"' in _read_line_with_timeout(
            proc.stdout, timeout=60
        ), "sidecar 未就绪"
        proc.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "run_example",
                    "params": {"id": DRILL_CACHE_NAME, "timeout": 300},
                }
            )
            + "\n"
        )
        proc.stdin.flush()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and not pid_file.exists():
            time.sleep(0.1)
        assert pid_file.exists(), "示例未启动"
        example_pid = int(pid_file.read_text(encoding="utf-8").strip())

        proc.terminate()  # 应用退出：SIGTERM 给 sidecar
        proc.wait(timeout=15)

        assert _pid_gone(
            example_pid, timeout=5
        ), f"sidecar 退出后示例进程 {example_pid} 仍存活（孤儿）"
    finally:
        if example_pid is not None:
            _kill_pid(example_pid)
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
        _cleanup_drill_cache()


# ------------------------------------------------------------- G6 用户集合


class _RpcEnv:
    """把 sidecar 的 store/索引/用户集合目录换到 tmp_path：任何写盘都落在临时目录。"""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.captured: list[dict] = []

    def __enter__(self) -> "_RpcEnv":
        self._orig = (
            server._store,
            server._root,
            dict(server._index),
            server.APP_DIR,
            server.DATA_DIR,
            server._USER_DIR,
        )
        coll = self.tmp_path / "json_examples"
        coll.mkdir(exist_ok=True)
        (coll / "builtin.json").write_text(
            json.dumps(
                {
                    "name": "builtin",
                    "examples": [{"id": "b1", "name": "b1.py", "code": "print(1)\n"}],
                }
            ),
            encoding="utf-8",
        )
        user_dir = self.tmp_path / "user_examples"
        user_dir.mkdir(exist_ok=True)
        server.APP_DIR = self.tmp_path
        server.DATA_DIR = self.tmp_path
        server._USER_DIR = user_dir
        server._store = None
        server._root = None
        server._index.clear()
        self._patch = patch.object(
            server, "_send", side_effect=lambda obj: self.captured.append(obj)
        )
        self._patch.start()
        return self

    def __exit__(self, *exc) -> bool:
        self._patch.stop()
        store, root, idx, app_dir, data_dir, user_dir = self._orig
        server._store = store
        server._root = root
        server.APP_DIR = app_dir
        server.DATA_DIR = data_dir
        server._USER_DIR = user_dir
        server._index.clear()
        server._index.update(idx)
        return False


def test_g6_reimport_dedupes_ids_across_collections(tmp_path):
    """同一源目录重复导入：id 全局去重（追加 _2），不得静默覆盖既有示例。"""
    with _RpcEnv(tmp_path) as env:
        src = tmp_path / "src"
        src.mkdir()
        (src / "hello.py").write_text("print('hi')\n", encoding="utf-8")

        server.method_import_examples(1, {"source_path": str(src), "name": "one"})
        server.method_import_examples(2, {"source_path": str(src), "name": "two"})

        assert env.captured[-1]["result"]["imported"] == 1
        assert {"b1", "hello.py", "hello.py_2"} <= set(server._index)
        collections = sorted(server._USER_DIR.glob("*.json"))
        assert len(collections) == 2
        ids_by_collection = []
        for f in collections:
            data = json.loads(f.read_text(encoding="utf-8"))
            ids_by_collection.append([s["id"] for s in data["examples"]])
        assert sorted(ids_by_collection[0] + ids_by_collection[1]) == [
            "hello.py",
            "hello.py_2",
        ]


def test_g6_import_midwrite_failure_leaves_no_partial_collection(tmp_path, monkeypatch):
    """导入写盘中途失败：不留半个集合文件、不留 .tmp，索引保持原样。"""
    with _RpcEnv(tmp_path) as env:
        src = tmp_path / "src"
        src.mkdir()
        (src / "mine.py").write_text("print(7)\n", encoding="utf-8")
        server._ensure_store()  # 先建索引，再取基线
        before_index = set(server._index)

        real_write_text = Path.write_text
        state = {"failed": False}

        def flaky(self, data, **kwargs):
            if not state["failed"] and str(self).startswith(str(server._USER_DIR)):
                state["failed"] = True
                with open(self, "w", encoding="utf-8"):
                    pass
                raise OSError("simulated mid-write failure")
            return real_write_text(self, data, **kwargs)

        monkeypatch.setattr(Path, "write_text", flaky)
        try:
            server.method_import_examples(1, {"source_path": str(src), "name": "mine"})
        finally:
            monkeypatch.undo()

        assert "error" in env.captured[0]
        assert list(server._USER_DIR.glob("*")) == [], "导入失败后残留了半成品文件"
        assert set(server._index) == before_index


def test_g6_import_without_candidates_writes_nothing(tmp_path):
    """源目录无可导入 .py 时不产生集合文件（空集合不落盘）。"""
    with _RpcEnv(tmp_path) as env:
        src = tmp_path / "src"
        src.mkdir()
        (src / "empty.py").write_text("", encoding="utf-8")

        server.method_import_examples(1, {"source_path": str(src), "name": "nada"})

        result = env.captured[0]["result"]
        assert result["imported"] == 0 and result["collection"] is None
        assert list(server._USER_DIR.glob("*.json")) == []
