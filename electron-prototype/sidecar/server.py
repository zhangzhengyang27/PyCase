#!/usr/bin/env python3
"""Electron + Python sidecar 最小原型。

通过 stdio 行分隔 JSON-RPC 2.0 与 Electron 主进程通信。
复用现有 app 包的 ExampleStore 加载示例，用 asyncio 子进程运行脚本
（替代原 QProcess 实现），输出通过 JSON-RPC notification 实时推送。

协议：
  请求:  {"jsonrpc":"2.0","id":1,"method":"list_examples","params":{}}
  响应:  {"jsonrpc":"2.0","id":1,"result":{...}}
  错误:  {"jsonrpc":"2.0","id":1,"error":{"code":-1,"message":"..."}}
  通知:  {"jsonrpc":"2.0","method":"run_output","params":{"run_id":"...","text":"..."}}
         {"jsonrpc":"2.0","method":"run_finished","params":{"run_id":"...","exit_code":0}}
"""

import ast
import asyncio
import base64
import json
import logging
import os
import shutil
import signal
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

# AI 代码解释（同目录模块，纯标准库）
import ai_service

# stdout 输出锁：AI 流式解释在工作线程中推送通知，需与主线程输出互斥
_STDOUT_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# 路径设置：把 APP_DIR / REPO_ROOT 插到 sys.path 最前，确保能 import app 包
# 且示例内部导入（兄弟模块、祖先包）能解析。app 是命名空间包，无需 editable 安装。
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # PyInstaller 打包模式：__file__ 指向临时解压目录，
    # 使用 cwd 作为基础目录（Electron 主进程 spawn 时设置了 cwd=APP_DIR）
    APP_DIR = Path(os.getcwd()).resolve()
    SCRIPT_DIR = APP_DIR / "electron-prototype" / "sidecar"
    PROTOTYPE_DIR = APP_DIR / "electron-prototype"
else:
    # 开发模式
    SCRIPT_DIR = Path(__file__).resolve().parent  # electron-prototype/sidecar
    PROTOTYPE_DIR = SCRIPT_DIR.parent  # electron-prototype
    APP_DIR = PROTOTYPE_DIR.parent  # desktop-app
# 仓库根（含 topics/tools/projects）：示例仓库已并入本项目时直接用 APP_DIR，
# 否则回退到上级目录（旧布局）
if all((APP_DIR / d).is_dir() for d in ("topics", "tools", "projects")):
    REPO_ROOT = APP_DIR
else:
    REPO_ROOT = APP_DIR.parent

# 可写数据根：打包模式下 APP_DIR（.app/Contents/Resources）只读且随升级重置，
# Electron 主进程注入 userData 存放 venv / 示例物化缓存 / 运行输出。
# 开发模式未注入时回退 APP_DIR，行为与旧版一致。
DATA_DIR = Path(os.environ.get("DESKTOP_APP_DATA_DIR") or APP_DIR).resolve()
# 用户示例集合目录（导入向导产物）：内置库只读捆绑，用户库可写、随应用数据存续
_USER_DIR = DATA_DIR / "user_examples"

for p in (str(APP_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# PyInstaller 冻结环境中 sys.executable 是 sidecar 自身，
# 运行示例与创建 venv 必须使用系统真实 Python
if getattr(sys, "frozen", False):
    # 优先复用已建好的项目共享 venv（.venv 在首次运行示例时创建）
    if sys.platform == "win32":
        _venv_python = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        _venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    REAL_PYTHON = (
        os.environ.get("PYTHON_EXECUTABLE")
        or (str(_venv_python) if _venv_python.exists() else None)
        or shutil.which("python3")
        or shutil.which("python")
        or sys.executable
    )
else:
    REAL_PYTHON = sys.executable

from app import importer  # noqa: E402
from app._version import __version__ as APP_VERSION  # noqa: E402
from app.contract_store import ContractStore  # noqa: E402
from app.logger import configure_logging, get_logger  # noqa: E402
from app.migration import migrate_user_collections  # noqa: E402
from app.models import ExampleItem  # noqa: E402
from app.venv_manager import VenvManager  # noqa: E402

# ---------------------------------------------------------------------------
# 运行时状态
# ---------------------------------------------------------------------------
_store: ContractStore | None = None
_root: ExampleItem | None = None
# example_id -> ExampleItem（扁平索引）
_index: dict[str, ExampleItem] = {}
# store 懒加载锁：预热线程与请求线程可能同时首次初始化，
# 无锁时 _rebuild_index 的 clear→fill 窗口会让并发 list_examples 读到空索引
_store_lock = threading.Lock()
# run_id -> asyncio.subprocess.Process（None 表示进程正在启动中）
_running: dict[str, asyncio.subprocess.Process | None] = {}
# 启动前就收到停止请求的 run_id 集合：进程启动后检查到此集合中的 id 则立即终止
_pending_stop: set[str] = set()
# run_id -> threading.Event（AI 解释取消标志，设置后流式读取中断）
_ai_running: dict[str, threading.Event] = {}
# 后台任务的强引用集合（asyncio 只弱引用 Task，见 method_run_example）
_bg_tasks: set[asyncio.Task] = set()
_venv_manager: VenvManager | None = None

# ---------------------------------------------------------------------------
# 环境准备状态（首启引导页与帮助面板消费；A5.5）
# ---------------------------------------------------------------------------
# 阶段推进顺序：preparing（建 venv 装依赖）→ indexing（建示例索引）→ warming（预检可运行性）→ ready
# 失败进 failed 并带原因；status 供轮询（首启页打开时补一次全量），progress 事件供增量推进
_ENV_LOG = DATA_DIR / "logs" / "sidecar.log"
_env_state: dict[str, Any] = {
    "phase": "starting",
    "failed_at": "",
    "started_at": time.time(),
    "error": "",
    "log_path": str(_ENV_LOG),
}
# 运行解释器模式：'shared'（默认，共享 venv）或 'system'（用户显式选择「用系统 Python 继续」）
_run_env_mode = "shared"


def _env_snapshot() -> dict[str, Any]:
    """环境状态快照：只读事实 + 解释器模式，缺的字段留空而不是编造。"""
    mgr = _get_venv_manager()
    venv_python = mgr.get_python_executable()
    snap: dict[str, Any] = dict(_env_state)
    snap["mode"] = _run_env_mode
    snap["venv_path"] = str(mgr.venv_path)
    snap["venv_ready"] = venv_python.exists() and not mgr.needs_prepare()
    snap["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    snap["examples"] = len(_index)
    snap["elapsed_ms"] = int((time.time() - float(_env_state.get("started_at") or time.time())) * 1000)
    return snap


def _set_env_phase(phase: str, error: str = "", failed_at: str = "") -> None:
    """推进环境阶段并广播（首启页据此显示步骤状态；失败带原因与失败的步骤）。"""
    _env_state["phase"] = phase
    _env_state["error"] = error
    _env_state["failed_at"] = failed_at
    _notify("env_progress", _env_snapshot())


def _on_bg_task_done(task: asyncio.Task) -> None:
    """后台任务收尾：解除强引用并把意外异常写入日志（而非静默消失）。"""
    _bg_tasks.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        get_logger(__name__).error("后台任务异常: %s", exc)


def _ensure_store() -> ContractStore:
    """懒加载 ExampleStore（首次调用时物化所有示例，可能较慢）。"""
    global _store, _root
    if _store is None:
        with _store_lock:
            if _store is None:
                store = _build_store()
                root = store.load()
                _rebuild_index(root)
                _store = store
                _root = root
    return _store


def _build_store() -> ContractStore:
    """构造契约 v2 存储：清单目录 + 集合树根 + 工作区根（可写根下）。

    - 内置清单在 ``APP_DIR/json_examples``；用户集合在可写根的 ``user_examples/``；
    - 集合树根 = REPO_ROOT（原位示例的 ``../topics`` 相对此根解析）；
    - 工作区根 = ``DATA_DIR/.json_examples_cache``（打包版 APP_DIR 只读，故用 DATA_DIR）。
    - 旧用户集合（v1 内联 code）在启动时自动迁移到 v2（契约 §2.4，含备份）。
    """
    migrate_user_collections(_USER_DIR, _USER_DIR.parent)
    return ContractStore(
        collection_dir=APP_DIR / "json_examples",
        data_root=REPO_ROOT,
        workspace_root=DATA_DIR / ".json_examples_cache",
        user_dir=_USER_DIR,
    )


def _reload_store() -> None:
    """重建 store/根树/索引（导入或删除用户集合后调用；锁内防竞态）。

    旧实例的模块索引直接转嫁（免一次子进程枚举）；可运行性缓存按 id 重算。
    """
    global _store, _root
    with _store_lock:
        old = _store
        store = _build_store()
        if old is not None and old._module_index is not None and old._module_index.available:
            store._module_index = old._module_index
        root = store.load()
        _rebuild_index(root)
        _store = store
        _root = root


def _get_venv_manager() -> VenvManager:
    """懒加载 VenvManager。"""
    global _venv_manager
    if _venv_manager is None:
        _venv_manager = VenvManager(repo_root=REPO_ROOT, python_exe=REAL_PYTHON, venv_root=DATA_DIR)
    return _venv_manager


def _rebuild_index(root: ExampleItem) -> None:
    """递归构建 example_id -> item 的扁平索引。"""
    _index.clear()

    def _walk(item: ExampleItem) -> None:
        if not item.is_dir and item.json_id:
            _index[item.json_id] = item
        for child in item.children:
            _walk(child)

    _walk(root)


def _item_to_dict(item: ExampleItem, include_code: bool = False) -> dict[str, Any]:
    """把 ExampleItem 序列化为可 JSON 化的字典。

    质量评分为惰性计算：加载时不做 AST 解析，首次序列化时才计算并缓存。
    include_code=False 用于目录树节点：树与 examples 数组共用此序列化，
    源码只需随数组传输一份。
    """
    store = _ensure_store()
    quality_score = store.ensure_quality_score(item)
    run_status = store.ensure_run_status(item)
    result = {
        "id": item.json_id or item.name,
        "name": item.name,
        "title": item.title,
        "category": item.category,
        "tags": item.tags,
        "quality_score": quality_score,
        "risk_high": store.ensure_risk_high(item),
        "run_status": run_status,
        "path": str(item.path),
        "source_dir": item.source_dir,
        "run_pythonpath": _ensure_store().run_pythonpath(item),
        "description": item.description or "",
        # 派生事实随列表下发（v2 不再传 code）：第三方 import 清单 + 命中主题
        "import_tags": store.import_tags(item),
        "theme_key": store.theme_key(item),
    }
    # 所属集合与来源标记（树节点与示例数组共用此序列化，两处一致）
    if item.parent is not None:
        result["collection"] = item.parent.name.removeprefix("📦 ")
    result["user_collection"] = store.is_user_collection(item.json_file)
    # HIGH 风险明细仅高危条目携带（全库十余条量级），供运行前确认弹窗展示
    if run_status == "risky" or result["risk_high"]:
        result["risk_findings"] = store.ensure_risk_findings(item)
    if include_code:
        # v2：源码按需从真实文件读（编辑器/AI/详情走这条），列表默认不带 code
        result["code"] = store.get_code(item)
    return result


# ---------------------------------------------------------------------------
# JSON-RPC 输出辅助
# ---------------------------------------------------------------------------
def _send(obj: dict[str, Any]) -> None:
    """写一行 JSON 到 stdout 并 flush。线程安全（AI 流式在线程中调用）。"""
    with _STDOUT_LOCK:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def _result(req_id: Any, result: Any) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _error(req_id: Any, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _notify(method: str, params: dict[str, Any]) -> None:
    _send({"jsonrpc": "2.0", "method": method, "params": params})


# ---------------------------------------------------------------------------
# 方法实现
# ---------------------------------------------------------------------------
def method_ping(req_id: Any, params: dict[str, Any]) -> None:
    _result(req_id, {"status": "ok", "python": sys.version.split()[0]})


def _tree_to_dict(item: ExampleItem) -> dict[str, Any]:
    """递归把 ExampleItem 树转为 JSON 友好的字典。"""
    node: dict[str, Any] = {
        "name": item.name,
        "type": "root" if item.category == "root" else ("collection" if item.is_dir else "example"),
        "is_dir": item.is_dir,
        "category": item.category,
        "children": [],
    }
    if not item.is_dir:
        # 示例节点携带元数据；完整源码只在 examples 数组发一份——
        # 1349 个示例的 code 重复序列化两份会让 list_examples 响应体翻倍
        node.update(_item_to_dict(item, include_code=False))
    for child in item.children:
        node["children"].append(_tree_to_dict(child))
    return node


def method_list_examples(req_id: Any, params: dict[str, Any]) -> None:
    store = _ensure_store()
    examples = [_item_to_dict(item) for item in _index.values()]
    tree = _tree_to_dict(_root) if _root else None
    _result(
        req_id,
        {
            "total": len(examples),
            "categories": list(store.categories),
            "examples": examples,
            "tree": tree,
        },
    )


def method_search_examples(req_id: Any, params: dict[str, Any]) -> None:
    """服务端检索：元数据内存匹配 + code 按需读文件（契约 §5）。

    返回 id 与命中原因，前端按 id 现有索引取卡片数据，避免把 code 全量下发。
    """
    store = _ensure_store()
    query = str(params.get("query") or "")
    try:
        limit = int(params.get("limit") or 50)
    except (TypeError, ValueError):
        limit = 50
    _result(req_id, {"query": query, "hits": store.search(query, limit=max(1, min(limit, 200)))})


def method_get_example(req_id: Any, params: dict[str, Any]) -> None:
    _ensure_store()
    example_id = params.get("id")
    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return
    _result(req_id, _item_to_dict(item, include_code=True))


async def method_run_example(req_id: Any, params: dict[str, Any]) -> None:
    """运行示例。立即返回 run_id，输出通过 notification 推送。"""
    _ensure_store()
    example_id = params.get("id")
    args = params.get("args") or []
    # args 逐项校验：非字符串元素会让 create_subprocess_exec 抛 TypeError，
    # 异常逃出后台协程后 run_finished 永不到达，前端会永远显示"运行中"
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        _error(req_id, -32602, "args 必须是字符串数组")
        return
    try:
        timeout = float(params.get("timeout", 30))
    except (TypeError, ValueError):
        timeout = 30.0

    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return

    run_id = uuid.uuid4().hex[:12]
    # 先注册为"启动中"（None），防止用户在子进程 spawn 前点击停止时
    # stop_run 找不到 run_id 而报错；_run_subprocess 启动后更新为实际进程
    _running[run_id] = None
    # 立即返回 run_id（不等待运行完成）
    _result(req_id, {"run_id": run_id})

    # 后台协程：启动子进程并流式推送输出。
    # 保存强引用：事件循环只弱引用 Task，无引用的任务可能在挂起期间被 GC
    task = asyncio.create_task(_run_subprocess(run_id, item, args, timeout))
    _bg_tasks.add(task)
    task.add_done_callback(_on_bg_task_done)


_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# 运行示例时允许传递的环境变量白名单：
# 不可信示例不应继承用户 shell 中的全部环境变量（可能含 API Key、令牌、密码等），
# 只保留 Python 运行所必需的、以及显式声明安全的变量。
_SAFE_ENV_VARS = frozenset(
    {
        # Python 运行必需
        "PATH",
        "PYTHONPATH",
        "PYTHONUNBUFFERED",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "HOME",
        "USER",
        "USERNAME",
        "TEMP",
        "TMP",
        "TMPDIR",
        # 系统/平台
        "OS",
        "SYSTEMROOT",
        "COMSPEC",
        "PATHEXT",
        # 显示相关（GUI 示例可能需要）
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XAUTHORITY",
        "XDG_RUNTIME_DIR",
        "XDG_SESSION_TYPE",
        # macOS 特定
        "__CF_USER_TEXT_ENCODING",
        "COMMAND_MODE",
    }
)


def _build_safe_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """构建运行示例用的安全环境变量：白名单过滤 + 额外注入。"""
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        if key in _SAFE_ENV_VARS:
            env[key] = value
    if extra:
        env.update(extra)
    return env


def _collect_images(working_dir: Path, since: float, limit: int = 12) -> list[str]:
    """递归扫描工作目录中本次运行生成的图片，返回 file:// URL 列表（按修改时间倒序）。

    只收集 mtime 不早于运行开始时间的文件，避免把历史残留图片也展示出来。
    递归扫描子目录（如 files/），确保脚本保存到相对子路径的结果图也能预览。
    """
    try:
        files = [p for p in working_dir.rglob("*") if p.is_file()]
    except OSError:
        return []
    files = [p for p in files if p.suffix.lower() in _IMAGE_EXTS]
    try:
        files = [p for p in files if p.stat().st_mtime >= since - 1]
    except OSError:
        pass
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.resolve().as_uri() for p in files[:limit]]


async def _run_subprocess(
    run_id: str,
    item: ExampleItem,
    args: list[str],
    timeout: float,
) -> None:
    """启动子进程运行示例，逐行读取输出并推送。"""
    # 契约 §4.1：运行前先确保工作区（唯一落盘入口），运行目录 = 工作区
    workspace = await asyncio.to_thread(_ensure_store().ensure_workspace, item)
    if workspace is None:
        _notify("run_output", {"run_id": run_id, "text": "[错误] 无法准备工作区，运行已取消\n"})
        _notify("run_finished", {"run_id": run_id, "exit_code": -1})
        return
    file_path = workspace / item.name
    working_dir = workspace
    run_started = time.time()

    # 通过 VenvManager 获取项目共享 venv 的解释器（首次运行时自动创建并预装常用库，
    # 示例目录的 requirements.txt 会装入同一环境）；阻塞操作放到线程池执行
    venv_mgr = _get_venv_manager()
    if _run_env_mode == "system":
        # 用户显式选择「用系统 Python 继续」：不碰共享环境，直接用系统解释器
        python_exe = REAL_PYTHON
        _notify(
            "run_output",
            {
                "run_id": run_id,
                "text": "[系统] 已按你的选择使用系统 Python（不覆盖共享环境）；缺依赖的示例会在此模式下报 ImportError\n",
            },
        )
    else:
        if venv_mgr.needs_prepare():
            _notify(
                "run_output",
                {
                    "run_id": run_id,
                    "text": "[系统] 首次运行：正在初始化共享运行环境（创建 venv 并安装常用依赖，约需几分钟）...\n",
                },
            )
            _set_env_phase("preparing")
        try:
            ok, python_exe = await asyncio.to_thread(venv_mgr.ensure_python, file_path)
            # 成功路径不输出环境噪音日志，仅在异常时提示回退
            if not ok:
                _notify(
                    "run_output",
                    {
                        "run_id": run_id,
                        "text": "[系统] 共享虚拟环境创建失败，回退系统 Python\n",
                    },
                )
                _set_env_phase("failed", "共享虚拟环境创建失败", failed_at="preparing")
        except Exception as e:  # noqa: BLE001
            _notify(
                "run_output",
                {
                    "run_id": run_id,
                    "text": f"[系统] 虚拟环境准备失败，回退系统 Python: {e}\n",
                },
            )
            _set_env_phase("failed", str(e), failed_at="preparing")
            python_exe = REAL_PYTHON

    # 构建环境变量：使用白名单过滤，避免把用户 shell 中的敏感环境变量
    # （API Key、令牌、密码等）传递给不可信示例
    # 运行期 sys.path：工作区（含基线兄弟文件）+ 集合树根（解析 topics/tools 包导入）
    pythonpath_parts = list(_ensure_store().run_pythonpath(item)) + [str(REPO_ROOT)]
    existing_pp = os.environ.get("PYTHONPATH", "")
    if existing_pp:
        pythonpath_parts.append(existing_pp)
    env = _build_safe_env(
        {
            "PYTHONPATH": os.pathsep.join(pythonpath_parts),
            "PYTHONUNBUFFERED": "1",
        }
    )

    cmd = [python_exe, str(file_path)] + list(args)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(working_dir),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # 合并输出，与原 MergedChannels 一致
            # 单行输出上限 8MB：默认 64KB 会让 print 超长行（如打印大列表）崩溃运行任务
            limit=8 * 1024 * 1024,
        )
    except OSError as e:
        _notify("run_output", {"run_id": run_id, "text": f"[错误] 无法启动子进程: {e}\n"})
        _notify("run_finished", {"run_id": run_id, "exit_code": -1})
        _pending_stop.discard(run_id)  # spawn 失败也要清理，避免集合泄漏
        return

    _running[run_id] = proc

    # 检查是否在启动前就收到了停止请求：如果是，立即终止
    if run_id in _pending_stop:
        _pending_stop.discard(run_id)
        _notify("run_output", {"run_id": run_id, "text": "[系统] 已在启动前收到停止指令，进程已终止\n"})
        _terminate(proc)
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            _kill(proc)
            await proc.wait()
        _running.pop(run_id, None)
        _notify("run_finished", {"run_id": run_id, "exit_code": -15})
        return

    async def _read_stream():
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            try:
                text = line.decode("utf-8")
            except UnicodeDecodeError:
                text = line.decode("gbk", errors="replace")
            _notify("run_output", {"run_id": run_id, "text": text})

    try:
        await asyncio.wait_for(_read_stream(), timeout=timeout + 5)
        exit_code = await asyncio.wait_for(proc.wait(), timeout=5)
    except asyncio.TimeoutError:
        _notify(
            "run_output",
            {
                "run_id": run_id,
                "text": f"\n[系统] 运行超过 {timeout} 秒，已强制终止。\n",
            },
        )
        _kill(proc)
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass  # 进程无法被 kill（如 D 状态），放弃等待，避免无限阻塞
        exit_code = -9
    except Exception as e:  # noqa: BLE001 - 输出流等异常也必须让 run_finished 到达前端
        _notify("run_output", {"run_id": run_id, "text": f"\n[系统] 输出流异常，已终止运行: {e}\n"})
        _kill(proc)
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass  # 同上，避免无限阻塞
        exit_code = -1
    finally:
        _running.pop(run_id, None)

    # 结束状态由前端结果面板徽章展示（成功/失败 + 退出码），不再推送日志文本
    # 扫描本次运行生成的图片并推送预览（PIL / 数据可视化 / OpenCV 等图形示例）
    # 保底：无论图片扫描是否异常，run_finished 必须到达前端，避免前端死锁
    try:
        images = _collect_images(working_dir, run_started)
        if images:
            _notify("run_images", {"run_id": run_id, "images": images})
    except Exception as e:  # noqa: BLE001
        get_logger(__name__).warning("扫描运行结果图片失败: %s", e)
    _notify("run_finished", {"run_id": run_id, "exit_code": exit_code})


def _terminate(proc: asyncio.subprocess.Process) -> None:
    """terminate 的安全封装：进程恰在收尾时可能已退出，ProcessLookupError 不算错误。"""
    try:
        proc.terminate()
    except ProcessLookupError:
        pass


def _kill(proc: asyncio.subprocess.Process) -> None:
    """kill 的安全封装：同 _terminate，SIGKILL 发给已 reap 的进程同样会抛错。"""
    try:
        proc.kill()
    except ProcessLookupError:
        pass


def _reap_sync(proc: asyncio.subprocess.Process, timeout: float) -> None:
    """同步等待并回收子进程（信号处理/退出路径不能 await）。

    与 asyncio 的子进程监视线程存在竞争：对方先 reap 时 os.waitpid 抛
    ChildProcessError，说明进程已消失，直接返回即可。
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            pid, _ = os.waitpid(proc.pid, os.WNOHANG)
        except (ChildProcessError, OSError):
            return
        if pid == proc.pid:
            return
        time.sleep(0.05)


def _terminate_all_running() -> None:
    """退出兜底：终止所有仍在运行的示例子进程，避免应用退出后留下孤儿。

    SIGTERM 处理与 stdin EOF 正常退出都走这里；幂等，可重复调用。
    先礼后兵：SIGTERM 给 3 秒体面退出，超时升级 SIGKILL。
    """
    procs = [p for p in list(_running.values()) if p is not None]
    for proc in procs:
        _terminate(proc)
    for proc in procs:
        _reap_sync(proc, timeout=3)
    for proc in procs:
        try:
            alive = proc.returncode is None and os.waitpid(proc.pid, os.WNOHANG) == (0, 0)
        except (ChildProcessError, OSError):
            alive = False
        if alive:
            _kill(proc)
            _reap_sync(proc, timeout=2)


async def method_stop_run(req_id: Any, params: dict[str, Any]) -> None:
    run_id = params.get("run_id")
    proc = _running.get(run_id)
    if run_id not in _running:
        _error(req_id, -32602, f"运行不存在或已结束: {run_id}")
        return
    if proc is None:
        # 进程正在启动中（spawn 尚未完成）：记录待停止，_run_subprocess 启动后立即终止
        _pending_stop.add(run_id)
        _result(req_id, {"status": "pending_terminate", "run_id": run_id})
        return
    _terminate(proc)
    _result(req_id, {"status": "terminating", "run_id": run_id})
    # 5 秒后进程仍未退出则升级为 SIGKILL（忽略 SIGTERM 的进程）
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except asyncio.TimeoutError:
        get_logger(__name__).warning("运行 %s 5 秒内未响应 SIGTERM，升级 SIGKILL", run_id)
        _kill(proc)




def _example_packages(store: ContractStore, item: ExampleItem) -> list[str]:
    """该示例要装的包：清单 requirements ∪ 派生 deps 的包名映射（去重、排序、剔本地/黑名单）。"""
    from app.facts import EXCLUDED_PKGS, _local_module_names, _norm_pkg  # 聚合口径单一来源
    from app.importer import IMPORT_TO_PKG

    entry = store._entry_of(item)
    names: set[str] = set()
    for req in (entry.requirements if entry else []) or []:
        pkg = _norm_pkg(str(req))
        if pkg and pkg not in EXCLUDED_PKGS:
            names.add(pkg)
    local = _local_module_names(REPO_ROOT)
    facts_entry = store._fact_entry(item) or {}
    for mod in facts_entry.get("deps") or []:
        if mod in local:
            continue
        pkg = _norm_pkg(IMPORT_TO_PKG.get(mod, mod))
        if pkg and pkg not in EXCLUDED_PKGS:
            names.add(pkg)
    return sorted(names)

# ---------------------------------------------------------------------------
# 存储治理（A6 缓存入口）：占用报告 / 两档清理 / v1 旧根回收
# ---------------------------------------------------------------------------
def method_storage_report(req_id: Any, params: dict[str, Any]) -> None:
    """返回工作区占用明细 + v1 旧根占用（设置中心「存储」分区的数据源）。"""
    _result(req_id, _ensure_store().storage_report())


def method_clean_workspace(req_id: Any, params: dict[str, Any]) -> None:
    """清理工作区：clean = 保留含用户资产的条目；all = 全部清理（用户显式选择）。"""
    mode = str(params.get("mode") or "clean")
    if mode not in ("clean", "all"):
        _error(req_id, -32602, "mode 必须是 clean 或 all")
        return
    _result(req_id, _ensure_store().clean_workspace(mode))


def method_reclaim_legacy_cache(req_id: Any, params: dict[str, Any]) -> None:
    """回收 v1 旧缓存根（缓存根下非 v2 内容），返回删除项数与释放字节。"""
    _result(req_id, _ensure_store().reclaim_legacy_cache())


# ---------------------------------------------------------------------------
# 编辑历史（A6 可恢复编辑）：列表 / 取内容 / 还原
# ---------------------------------------------------------------------------
def _history_item(example_id: Any) -> ExampleItem | None:
    """按 id 取示例（历史相关方法共用；不存在返回 None，由调用方报错）。"""
    _ensure_store()
    item = _index.get(example_id)
    return item if isinstance(example_id, str) else None


def method_list_versions(req_id: Any, params: dict[str, Any]) -> None:
    item = _history_item(params.get("id"))
    if item is None:
        _error(req_id, -32602, f"示例不存在: {params.get('id')}")
        return
    _result(req_id, {"id": item.json_id, "versions": _ensure_store().list_versions(item)})


def method_read_version(req_id: Any, params: dict[str, Any]) -> None:
    item = _history_item(params.get("id"))
    if item is None:
        _error(req_id, -32602, f"示例不存在: {params.get('id')}")
        return
    ts = str(params.get("ts") or "")
    content = _ensure_store().read_version(item, ts)
    if content is None:
        _error(req_id, -32602, f"版本不存在: {ts}")
        return
    _result(req_id, {"id": item.json_id, "ts": ts, "code": content})


def method_restore_version(req_id: Any, params: dict[str, Any]) -> None:
    """还原到某份历史版本（还原前会对当前内容再留一份快照，可反复回退）。"""
    item = _history_item(params.get("id"))
    if item is None:
        _error(req_id, -32602, f"示例不存在: {params.get('id')}")
        return
    ts = str(params.get("ts") or "")
    if not _ensure_store().restore_version(item, ts):
        _error(req_id, -32600, f"还原失败（版本不存在或写盘失败）: {ts}")
        return
    _result(req_id, {"id": item.json_id, "restored": ts})


# ---------------------------------------------------------------------------
# 缺依赖修复（A6 失败恢复）：按派生 import 分析装包并刷新模块索引
# ---------------------------------------------------------------------------
async def method_install_example_deps(req_id: Any, params: dict[str, Any]) -> None:
    """把该示例的依赖装进共享 venv：清单 requirements ∪ 派生 import 分析（去本地模块/黑名单）。

    装完刷新模块索引，让画廊的可运行性徽章立即反映新环境；随后前端可自动重跑。
    """
    store = _ensure_store()
    item = _history_item(params.get("id"))
    if item is None:
        _error(req_id, -32602, f"示例不存在: {params.get('id')}")
        return
    packages = _example_packages(store, item)
    if not packages:
        _result(req_id, {"installed": [], "failed": [], "packages": []})
        return
    mgr = _get_venv_manager()
    installed, failed = await asyncio.to_thread(mgr.install_packages, packages)
    if installed:
        # 环境变了：刷新模块索引并清掉可运行性缓存
        try:
            store.set_module_python(str(mgr.get_python_executable()))
        except Exception as e:  # noqa: BLE001 - 索引刷新失败不影响"已装包"这个事实
            get_logger(__name__).warning("刷新模块索引失败: %s", e)
    _result(req_id, {"installed": installed, "failed": failed, "packages": packages})

# ---------------------------------------------------------------------------
# argparse 静态分析（AST，无需执行代码）
# ---------------------------------------------------------------------------
def _ast_constant(node: ast.AST) -> Any:
    """从 AST 节点提取常量值；非字面量节点（动态表达式）返回 None。

    仅支持 ast.Constant：ast.Num/Str/NameConstant 兼容别名在 Python 3.14
    已被移除，访问即抛 AttributeError，不得引用。
    """
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _ast_name(node: ast.AST) -> str | None:
    """从 AST 节点提取名称（如 int, str, float）。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _parse_argparse_from_code(code: str) -> list[dict[str, Any]]:
    """静态分析 Python 代码中的 argparse.add_argument 调用，返回参数规格列表。

    每个参数字典包含：
      - name: 显示名（如 --name 或位置参数名）
      - flags: 命令行 flag 列表（如 ["--name", "-n"]），位置参数为空列表
      - dest: 参数变量名
      - type: 类型名（str/int/float/bool），默认 str
      - default: 默认值
      - help: 帮助文本
      - choices: 可选值列表
      - required: 是否必填
      - action: action 类型（store/store_true/store_false 等）
      - is_positional: 是否为位置参数
      - nargs: nargs 说明
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    args_specs: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue

        # 第一个位置参数（或前几个）是 flag 名
        flags: list[str] = []
        positional_name: str | None = None
        for arg in node.args:
            val = _ast_constant(arg)
            if isinstance(val, str):
                if val.startswith("-"):
                    flags.append(val)
                elif positional_name is None:
                    positional_name = val

        is_positional = len(flags) == 0

        # 解析关键字参数
        kw: dict[str, Any] = {}
        for kwnode in node.keywords:
            key = kwnode.arg
            if key is None:
                continue
            if key == "type":
                kw["type"] = _ast_name(kwnode.value) or "str"
            elif key == "default":
                kw["default"] = _ast_constant(kwnode.value)
            elif key == "help":
                help_val = _ast_constant(kwnode.value)
                kw["help"] = help_val if isinstance(help_val, str) else ""
            elif key == "required":
                req_val = _ast_constant(kwnode.value)
                kw["required"] = bool(req_val) if req_val is not None else False
            elif key == "action":
                action_val = _ast_constant(kwnode.value)
                kw["action"] = action_val if isinstance(action_val, str) else "store"
            elif key == "choices":
                choices: list[Any] = []
                if isinstance(kwnode.value, (ast.List, ast.Tuple)):
                    for elt in kwnode.value.elts:
                        v = _ast_constant(elt)
                        if v is not None:
                            choices.append(v)
                kw["choices"] = choices
            elif key == "nargs":
                nargs_val = _ast_constant(kwnode.value)
                kw["nargs"] = nargs_val if isinstance(nargs_val, (str, int)) else None
            elif key == "metavar":
                meta_val = _ast_constant(kwnode.value)
                kw["metavar"] = meta_val if isinstance(meta_val, str) else None

        # 推导 dest
        if is_positional:
            dest = positional_name or f"arg{len(args_specs)}"
            display_name = dest
        else:
            # 取第一个长 flag 去掉 -- 作为 dest
            long_flag = next((f for f in flags if f.startswith("--")), flags[0])
            dest = long_flag.lstrip("-").replace("-", "_")
            display_name = flags[0]

        action = kw.get("action", "store")
        arg_type = kw.get("type", "str")
        # store_true/store_false 隐含 bool 类型且无 default 时默认 False
        if action in ("store_true", "store_false"):
            arg_type = "bool"
            if "default" not in kw:
                kw["default"] = action == "store_false"

        spec = {
            "name": display_name,
            "flags": flags,
            "dest": dest,
            "type": arg_type,
            "default": kw.get("default"),
            "help": kw.get("help", ""),
            "choices": kw.get("choices", []),
            "required": kw.get("required", False) and not is_positional,
            "action": action,
            "is_positional": is_positional,
            "nargs": kw.get("nargs"),
            "metavar": kw.get("metavar"),
        }
        args_specs.append(spec)

    return args_specs


def method_parse_args(req_id: Any, params: dict[str, Any]) -> None:
    """静态分析示例代码中的 argparse 定义，返回参数规格。"""
    example_id = params.get("id")
    code = params.get("code")

    if code is None:
        _ensure_store()
        item = _index.get(example_id)
        if item is None:
            _error(req_id, -32602, f"示例不存在: {example_id}")
            return
        # v2：源码经 store 按需读（v1 兼容期读内联 code，迁移后读真实文件）
        code = _ensure_store().get_code(item)

    specs = _parse_argparse_from_code(code)
    _result(req_id, {"args": specs, "count": len(specs)})


def method_save_example(req_id: Any, params: dict[str, Any]) -> None:
    """保存编辑：契约 v2 下写真实文件（清单只存元数据，不再回写内联 code）。"""
    example_id = params.get("id")
    new_code = params.get("code")

    if example_id is None or new_code is None:
        _error(req_id, -32602, "缺少 id 或 code 参数")
        return

    _ensure_store()
    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return

    success = _store.save_item(item, new_code)
    if success:
        _result(
            req_id,
            {
                "status": "saved",
                "id": example_id,
                "json_file": str(item.json_file) if item.json_file else None,
                "path": str(item.path),
            },
        )
    else:
        _error(req_id, -32000, "保存失败：该示例可能不是 JSON 来源或写入出错")


# ---------------------------------------------------------------------------
# 示例资源文件（详情页上传图片/文档，运行时可直接用文件名引用）
# ---------------------------------------------------------------------------
_IMAGE_EXTS_ASSET = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def _asset_dir(item: ExampleItem) -> Path:
    """示例的资源目录 = 运行工作区（契约 §4.1：资源上传/列举先经唯一落盘入口）。

    ensure_workspace 负责建目录与自愈重建；失败时仍返回工作区路径，
    由调用方的写盘/遍历报错兜底（不静默）。
    """
    store = _ensure_store()
    store.ensure_workspace(item)
    return store.workspace_of(item)


def _safe_asset_name(filename: str) -> str:
    """只保留文件名，防止路径穿越。"""
    return Path(filename or "").name or "uploaded_file"


# 资源写入/删除的保护名单：上传同名脚本会产生"编辑器显示 JSON 代码、
# 实际执行上传内容"的所见非所跑；覆盖 requirements.txt 则可向共享 venv 任意装包；
# 工作区账本 .manifest.json（契约 §4.2）被覆盖会丢失基线记录。
def _is_protected_asset(item: ExampleItem, filename: str) -> bool:
    lowered = filename.lower()
    if lowered.endswith(".py") or lowered in ("requirements.txt", ".manifest.json"):
        return True
    return filename == item.path.name


def _collect_assets(item: ExampleItem) -> list[dict[str, Any]]:
    """列出工作区中的用户资源文件。

    排除受保护文件（示例脚本、__init__.py、requirements.txt、工作区账本
    .manifest.json）：它们不可删除或属于内部数据，列进资源面板只会给出
    "能删但删不掉"的死入口（A4 走查发现）。
    """
    d = _asset_dir(item)
    assets = []
    try:
        for p in sorted(d.iterdir()):
            if not p.is_file():
                continue
            if _is_protected_asset(item, p.name):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            is_image = p.suffix.lower() in _IMAGE_EXTS_ASSET
            assets.append(
                {
                    "filename": p.name,
                    "size": st.st_size,
                    "modified": round(st.st_mtime, 3),
                    "is_image": is_image,
                }
            )
    except OSError:
        pass
    return assets


def method_upload_asset(req_id: Any, params: dict[str, Any]) -> None:
    """把前端上传的图片/文档保存到示例运行目录（base64）。"""
    example_id = params.get("id")
    filename = params.get("filename")
    data = params.get("data")
    if example_id is None or filename is None or data is None:
        _error(req_id, -32602, "缺少 id / filename / data 参数")
        return
    _ensure_store()
    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return
    try:
        raw = base64.b64decode(data, validate=False)
    except Exception as e:  # noqa: BLE001
        _error(req_id, -32602, f"base64 解码失败: {e}")
        return
    safe = _safe_asset_name(filename)
    if _is_protected_asset(item, safe):
        _error(req_id, -32602, f"不允许上传该文件名（可能与示例脚本/依赖清单冲突）: {safe}")
        return
    target = _asset_dir(item) / safe
    try:
        target.write_bytes(raw)
    except OSError as e:
        _error(req_id, -32000, f"写入失败: {e}")
        return
    _result(
        req_id,
        {
            "status": "uploaded",
            "filename": safe,
            "size": len(raw),
            "path": str(target),
            "assets": _collect_assets(item),
        },
    )


def method_list_assets(req_id: Any, params: dict[str, Any]) -> None:
    """列出示例目录中的资源文件。"""
    example_id = params.get("id")
    if example_id is None:
        _error(req_id, -32602, "缺少 id 参数")
        return
    _ensure_store()
    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return
    _result(req_id, {"assets": _collect_assets(item)})


def method_delete_asset(req_id: Any, params: dict[str, Any]) -> None:
    """删除示例目录中的某个资源文件。"""
    example_id = params.get("id")
    filename = params.get("filename")
    if example_id is None or filename is None:
        _error(req_id, -32602, "缺少 id 或 filename 参数")
        return
    _ensure_store()
    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return
    safe = _safe_asset_name(filename)
    if _is_protected_asset(item, safe):
        _error(req_id, -32602, f"不允许删除该文件（示例脚本/依赖清单受保护）: {safe}")
        return
    target = _asset_dir(item) / safe
    try:
        if target.exists() and target.is_file():
            target.unlink()
            _result(req_id, {"deleted": safe, "assets": _collect_assets(item)})
        else:
            _error(req_id, -32000, f"文件不存在: {safe}")
    except OSError as e:
        _error(req_id, -32000, f"删除失败: {e}")


# ---------------------------------------------------------------------------
# 用户示例集合导入/删除（示例库与应用解耦）
# ---------------------------------------------------------------------------
def _import_availability():
    """依赖猜测的可用性谓词：优先共享 venv 模块索引（与可运行性判定同源），
    索引未就绪时退化为当前解释器的 find_spec（importer 缺省行为）。"""
    store = _ensure_store()
    idx = store._module_index  # noqa: SLF001 - 模块内访问自有 store
    if idx is not None and idx.available:
        return idx.is_available
    return None


def method_scan_import_source(req_id: Any, params: dict[str, Any]) -> None:
    """扫描待导入目录，返回预览清单（不写盘、不改动集合）。

    预览 id 与随后 import_examples 的最终 id 一致（同 existing_ids 去重口径）。
    """
    source = Path(str(params.get("source_path") or ""))
    if not source.is_dir():
        _error(req_id, -32602, f"目录不存在: {source}")
        return
    _ensure_store()
    payload = importer.import_directory(
        source, "preview", existing_ids=set(_index.keys()), is_available=_import_availability()
    )
    # 预览不回传完整 code（大目录体积可观），回传大小供 UI 展示
    files = [
        {
            "id": ex["id"],
            "name": ex["name"],
            "tags": ex["tags"],
            "requirements": ex["requirements"],
            "bytes": len(ex["code"].encode("utf-8")),
        }
        for ex in payload["examples"]
    ]
    _result(req_id, {"total": payload["stats"]["scanned"], "files": files, "skipped": payload["skipped"]})


def method_import_examples(req_id: Any, params: dict[str, Any]) -> None:
    """把目录导入为用户集合：构建 payload → id 去重 → 原子写 JSON → 重建索引。"""
    source = Path(str(params.get("source_path") or ""))
    name = str(params.get("name") or "").strip() or source.name
    if not source.is_dir():
        _error(req_id, -32602, f"目录不存在: {source}")
        return
    _ensure_store()
    payload = importer.import_directory(
        source, name, existing_ids=set(_index.keys()), is_available=_import_availability()
    )
    imported = payload["examples"]
    if not imported:
        _result(req_id, {"imported": 0, "skipped": payload["skipped"], "collection": None})
        return

    _USER_DIR.mkdir(parents=True, exist_ok=True)
    # 全中文等非 ASCII 名称 slug 化后只剩下划线，回退通用名
    slug = importer.slugify(name).strip("_") or "user_collection"
    n = 0
    manifest_path = None
    while manifest_path is None:
        candidate = slug if n == 0 else f"{slug}_{n + 1}"
        if not (_USER_DIR / f"{candidate}.json").exists() and not (_USER_DIR / candidate).exists():
            manifest_path = candidate
        n += 1
    try:
        # 契约 v2：先落真实源码（暂存目录整体 rename）→ 原子替换清单 → 失败回滚
        importer.write_user_collection(
            _USER_DIR, manifest_path, name, payload["description"], imported
        )
    except OSError as e:
        _error(req_id, -32603, f"写入用户集合失败: {e}")
        return
    _reload_store()
    _result(
        req_id,
        {
            "imported": len(imported),
            "skipped": payload["skipped"],
            "collection": manifest_path,
            "total": len(_index),
        },
    )


def method_delete_example(req_id: Any, params: dict[str, Any]) -> None:
    """删除一个用户集合示例（内置集合受保护，sidecar 侧再校验一次）。"""
    _ensure_store()
    example_id = str(params.get("id") or "")
    item = _index.get(example_id)
    if item is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return
    if not _store.is_user_collection(item.json_file):
        _error(req_id, -32602, "仅可删除用户集合中的示例")
        return
    if not _store.delete_user_example(item):
        _error(req_id, -32603, f"删除失败: {example_id}")
        return
    _reload_store()
    _result(req_id, {"deleted": example_id, "total": len(_index)})


async def method_explain_code(req_id: Any, params: dict[str, Any]) -> None:
    """AI 代码解释（DeepSeek 流式）。立即返回 run_id，chunk 通过 notification 推送。

    params: {code, api_key, file_name?, context?, base_url?, model?, timeout?}
    通知: ai_explain_chunk {run_id, text}
          ai_explain_done  {run_id, full_text, model, tokens}
          ai_explain_error {run_id, error}
    """
    code = params.get("code", "")
    api_key = params.get("api_key", "")
    run_id = params.get("run_id") or uuid.uuid4().hex[:12]

    # 参数转换/校验全部前置：首响应发出后再转换会让坏参数对同一 req_id
    # 先发 result 再发 error，违反 JSON-RPC 一请求一响应
    file_name = str(params.get("file_name") or "")
    context = str(params.get("context") or "")
    base_url = str(params.get("base_url") or ai_service.DEFAULT_BASE_URL)
    model = str(params.get("model") or ai_service.DEFAULT_MODEL)
    try:
        timeout = int(params.get("timeout") or ai_service.DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        timeout = ai_service.DEFAULT_TIMEOUT

    # 无 key 或空代码：同步返回错误，不启动流
    if not api_key or not str(api_key).strip():
        _result(req_id, {"run_id": run_id, "status": "error", "error": "no_api_key"})
        return
    if not code or not str(code).strip():
        _result(req_id, {"run_id": run_id, "status": "error", "error": "empty_code"})
        return

    _result(req_id, {"run_id": run_id, "status": "started"})

    cancel_event = threading.Event()
    _ai_running[run_id] = cancel_event

    def on_chunk(text: str) -> None:
        _notify("ai_explain_chunk", {"run_id": run_id, "text": text})

    try:
        # urllib 阻塞，放到工作线程避免阻塞 JSON-RPC 事件循环
        result = await asyncio.to_thread(
            ai_service.explain_code_streaming,
            str(code),
            str(api_key),
            file_name=file_name,
            context=context,
            base_url=base_url,
            model=model,
            timeout=timeout,
            on_chunk=on_chunk,
            cancel_event=cancel_event,
        )
    except Exception as e:  # noqa: BLE001 - 前端只认 ai_explain_error 通知，异常必须转成通知
        get_logger(__name__).warning("AI 解释内部异常 run_id=%s: %s", run_id, e)
        result = {"ok": False, "error": f"internal: {e}", "full_text": "", "model": model, "tokens": 0}
    finally:
        _ai_running.pop(run_id, None)

    if result.get("ok"):
        _notify(
            "ai_explain_done",
            {
                "run_id": run_id,
                "full_text": result.get("full_text", ""),
                "model": result.get("model", ""),
                "tokens": result.get("tokens", 0),
            },
        )
    else:
        _notify("ai_explain_error", {"run_id": run_id, "error": result.get("error", "unknown")})


def method_stop_ai(req_id: Any, params: dict[str, Any]) -> None:
    """停止正在进行的 AI 解释（设置 cancel_event，流式读取会在下一行中断）。"""
    run_id = params.get("run_id")
    event = _ai_running.get(run_id)
    if event is None:
        _error(req_id, -32602, f"AI 解释不存在或已结束: {run_id}")
        return
    event.set()
    _result(req_id, {"status": "cancelled", "run_id": run_id})


# ---------------------------------------------------------------------------
# 方法分发表
# ---------------------------------------------------------------------------
def method_env_status(req_id: Any, params: dict[str, Any]) -> None:
    """返回环境准备状态快照（首启引导页/帮助面板消费）。"""
    _result(req_id, _env_snapshot())


def method_set_run_env(req_id: Any, params: dict[str, Any]) -> None:
    """切换运行解释器模式：shared（默认，共享 venv）或 system（用系统 Python 继续）。"""
    global _run_env_mode
    mode = str(params.get("mode") or "")
    if mode not in ("shared", "system"):
        _error(req_id, -32602, "mode 必须是 shared 或 system")
        return
    _run_env_mode = mode
    get_logger(__name__).info("运行解释器模式切换为: %s", mode)
    _result(req_id, _env_snapshot())


METHODS = {
    "ping": method_ping,
    "env_status": method_env_status,
    "set_run_env": method_set_run_env,
    "list_examples": method_list_examples,
    "get_example": method_get_example,
    "search_examples": method_search_examples,
    "parse_args": method_parse_args,
    "save_example": method_save_example,
    "run_example": method_run_example,  # async
    "stop_run": method_stop_run,
    "upload_asset": method_upload_asset,
    "list_assets": method_list_assets,
    "delete_asset": method_delete_asset,
    "scan_import_source": method_scan_import_source,
    "import_examples": method_import_examples,
    "delete_example": method_delete_example,
    "explain_code": method_explain_code,  # async，流式
    "stop_ai": method_stop_ai,
    # A6：存储治理 / 编辑历史 / 缺依赖修复
    "storage_report": method_storage_report,
    "clean_workspace": method_clean_workspace,
    "reclaim_legacy_cache": method_reclaim_legacy_cache,
    "list_versions": method_list_versions,
    "read_version": method_read_version,
    "restore_version": method_restore_version,
    "install_example_deps": method_install_example_deps,  # async
}


async def _handle_request(line: str) -> None:
    """处理一行 JSON-RPC 请求。"""
    line = line.strip()
    if not line:
        return
    try:
        req = json.loads(line)
    except json.JSONDecodeError as e:
        _error(None, -32700, f"JSON 解析失败: {e}")
        return

    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
        _error(req.get("id") if isinstance(req, dict) else None, -32600, "无效的 JSON-RPC 2.0 请求")
        return

    method_name = req.get("method")
    params = req.get("params") or {}
    req_id = req.get("id")

    handler = METHODS.get(method_name)
    if handler is None:
        _error(req_id, -32601, f"未知方法: {method_name}")
        return

    try:
        result = handler(req_id, params)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:  # noqa: BLE001 - sidecar 不应崩溃
        _error(req_id, -32603, f"内部错误: {e}")


async def _stdin_reader() -> None:
    """从 stdin 逐行读取请求并处理。"""
    loop = asyncio.get_event_loop()
    # 默认 limit=64KB：上传 base64 图片/文档会触发 LimitOverrunError 导致 sidecar 崩溃。
    # 提高到 128MB，足以容纳单次上传的资源文件。
    reader = asyncio.StreamReader(limit=128 * 1024 * 1024)
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        try:
            line = await reader.readline()
        except (ValueError, asyncio.LimitOverrunError) as e:
            # 单行超过 128MB 缓冲上限：丢弃该行并保持进程存活，而不是崩出事件循环
            get_logger(__name__).error("请求行超出缓冲上限，已丢弃: %s", e)
            continue
        if not line:
            break
        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError:
            continue
        try:
            await _handle_request(text)
        except Exception as e:  # noqa: BLE001 - 单条请求的意外异常不得杀死整个 sidecar
            get_logger(__name__).exception("处理请求时发生未捕获异常: %s", e)


def _warmup_venv() -> None:
    """后台预热共享 venv：创建 .venv 并预装常用依赖，用户浏览界面时并行完成。

    每推进一步都广播 env_progress（首启引导页据此显示步骤状态），失败带原因；
    预热失败不影响 sidecar 本身，首次运行时会重试。
    """
    try:
        _set_env_phase("preparing")
        if _run_env_mode == "system":
            get_logger(__name__).info("已选择系统解释器模式，跳过共享环境准备")
            _set_env_phase("ready")
            return
        if _get_venv_manager().prepare():
            get_logger(__name__).info("共享运行环境已就绪: %s", _get_venv_manager().venv_path)
            _set_env_phase("indexing")
            # venv 就绪后构建模块索引并批量预热可运行性状态，
            # 让画廊首屏就带 run_status 徽章（判定全部为内存集合运算）
            store = _ensure_store()
            store.set_module_python(str(_get_venv_manager().get_python_executable()))
            _set_env_phase("warming")
            _ = [store.ensure_run_status(it) for it in list(_index.values())]
            get_logger(__name__).info("可运行性状态预热完成: %d 个示例", len(_index))
            _set_env_phase("ready")
        else:
            _set_env_phase("failed", "共享依赖安装未完成", failed_at="preparing")
    except Exception as e:  # noqa: BLE001 - 预热失败不影响 sidecar，首次运行时会重试
        get_logger(__name__).warning("共享运行环境预热失败: %s", e)
        _set_env_phase("failed", str(e), failed_at=str(_env_state.get("phase") or "preparing"))


def _on_terminate_signal(signum, _frame) -> None:
    """SIGTERM/SIGINT：先杀正在运行的示例，再让进程退出（不留孤儿）。

    处理函数在主线程同步执行；asyncio 事件循环收到 EINTR 后重新调度本函数，
    SystemExit 从信号点向上传播，main 的 finally 再兜一次清理（幂等）。
    """
    get_logger(__name__).info("收到信号 %s，正在清理运行中的示例进程", signum)
    _terminate_all_running()
    raise SystemExit(128 + signum)


def main() -> None:
    """sidecar 入口。"""
    # 强制 stdout/stderr 为 UTF-8：Windows 下管道默认 ANSI 代码页（如 cp936），
    # ensure_ascii=False 输出的中文/emoji 会触发 UnicodeEncodeError——
    # 轻则误杀正在运行的示例，重则 AI 流式中断且前端收不到 error 通知
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    # INFO 级日志走 stderr（不污染 JSON-RPC stdout），否则 venv 创建等关键过程不可见
    _ENV_LOG.parent.mkdir(parents=True, exist_ok=True)
    configure_logging(level=logging.INFO, log_file=str(_ENV_LOG))
    # 应用退出信号：必须在事件循环启动前注册，否则窗口关闭到信号送达之间
    # 运行的示例会因 sidecar 直接终止而成为孤儿（G5）
    for _sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(_sig, _on_terminate_signal)
        except (ValueError, OSError):  # 非主线程/平台不支持时保持默认行为
            pass
    # 启动时发一条 ready 通知，让 Electron 知道 sidecar 已就绪
    _notify("sidecar_ready", {"version": APP_VERSION, "app_dir": str(APP_DIR)})
    # 后台预热共享 venv（线程内阻塞安装依赖，不阻碍 JSON-RPC 事件循环）
    threading.Thread(target=_warmup_venv, name="venv-warmup", daemon=True).start()
    try:
        asyncio.run(_stdin_reader())
    except KeyboardInterrupt:
        pass
    finally:
        # stdin EOF（父进程关闭管道）与信号路径都兜底：不能留下孤儿示例
        _terminate_all_running()


if __name__ == "__main__":
    main()
