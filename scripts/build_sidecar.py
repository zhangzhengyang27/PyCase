#!/usr/bin/env python3
"""冻结 Python sidecar 为独立可执行文件，并冒烟验证（打包链的可复现入口）。

为什么要有这个脚本：原先 `sidecar-dist/` 是手工产物（且仓库里并不存在），
electron-builder 的 extraResources 指向它——打包不可复现（审计 C1）。现在：

    python scripts/build_sidecar.py            # 冻结到 electron-prototype/electron/sidecar-dist/
    python scripts/build_sidecar.py --smoke    # 冻结后跑冒烟：真启动 + list_examples == 1493

产物名随平台（sidecar / sidecar.exe），与 package.json 的 extraResources 约定一致。

冒烟为什么要塞一个假解释器：sidecar 启动会在后台线程预热共享 venv（装 46 个包，需网络）。
打包验证要的是「冻结产物能启动、能加载 app 包、能读资源里的数据」，不是重装依赖，
因此把 PYTHON_EXECUTABLE 指到不存在的路径让预热快速失败（侧车本身就是这么设计降级的）。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

# Windows 控制台默认 cp1252，本脚本的中文输出会 UnicodeEncodeError（CI 上真踩过）；
# 日志侧（GitHub Actions）按 UTF-8 解码，这里统一改 UTF-8 并对个别字符降级
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
ELECTRON_DIR = ROOT / "electron-prototype" / "electron"
SPEC = ELECTRON_DIR / "build-pyinstaller" / "sidecar.spec"
OUT_DIR = ELECTRON_DIR / "sidecar-dist"
EXPECTED_EXAMPLES = 1493


def _binary_name() -> str:
    return "sidecar.exe" if sys.platform == "win32" else "sidecar"


def build() -> Path:
    """跑 PyInstaller；返回产物路径（缺失即构建失败）。"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = ELECTRON_DIR / "build-pyinstaller" / "work"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(OUT_DIR),
        "--workpath",
        str(work),
        str(SPEC),
    ]
    print(f"[sidecar] 冻结中: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(ELECTRON_DIR))
    if proc.returncode != 0:
        raise SystemExit(f"[sidecar] PyInstaller 失败（退出码 {proc.returncode}）")
    binary = OUT_DIR / _binary_name()
    if not binary.is_file():
        raise SystemExit(f"[sidecar] 未找到产物: {binary}")
    print(f"[sidecar] 产物: {binary} ({binary.stat().st_size / 1024 / 1024:.1f} MiB)")
    return binary


def _read_line(stream, box: list[str], timeout: float) -> str | None:
    t = threading.Thread(target=lambda: box.append(stream.readline()), daemon=True)
    t.start()
    t.join(timeout)
    return box[0] if box else None


def smoke(binary: Path) -> None:
    """真启动冻结产物：sidecar_ready → list_examples == 期望条数 → ping。

    cwd 用仓库根：冻结模式下 APP_DIR = cwd，仓库根正好具备
    topics/tools/projects/json_examples 的布局，等价于打包后的 resources 目录。
    stderr 落盘而不是丢弃：Windows CI 上「发完 sidecar_ready 就没响应」这类失败，
    stderr 里的 traceback 是唯一现场，吞掉就只能盲猜。
    """
    data_dir = Path(tempfile.mkdtemp(prefix="sidecar-smoke-"))
    err_log = data_dir / "sidecar-stderr.log"
    env = {
        **os.environ,
        "DESKTOP_APP_DATA_DIR": str(data_dir),
        "PYTHON_EXECUTABLE": str(data_dir / "no-such-python"),  # 短路 venv 预热，见文件头注释
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
    }
    err_file = err_log.open("wb")
    proc = subprocess.Popen(
        [str(binary)],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=err_file,
        text=True,
        encoding="utf-8",
        env=env,
    )
    try:
        assert proc.stdout is not None and proc.stdin is not None
        line = _read_line(proc.stdout, [], timeout=90)
        if not line or "sidecar_ready" not in line:
            raise SystemExit(f"[sidecar] 启动失败（未收到 sidecar_ready）: {line!r}")
        print("[sidecar] sidecar_ready ✓")

        def call(req_id: int, method: str, params: dict) -> dict:
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n")
            proc.stdin.flush()
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                box: list[str] = []
                got = _read_line(proc.stdout, box, timeout=deadline - time.monotonic())
                if got is None:
                    raise SystemExit(f"[sidecar] {method} 等待超时（120s 内没有该 id 的响应）")
                if got == "":
                    # stdout 被关闭 = sidecar 进程已经没了，报"超时"会把人带偏
                    raise SystemExit(f"[sidecar] {method} 无响应：sidecar 已退出（退出码 {proc.poll()}）")
                try:
                    msg = json.loads(got)
                except json.JSONDecodeError:
                    continue
                if msg.get("id") == req_id:
                    return msg
            raise SystemExit(f"[sidecar] {method} 等待超时")

        ping = call(1, "ping", {})
        if ping.get("result", {}).get("status") != "ok":
            raise SystemExit(f"[sidecar] ping 失败: {ping}")
        print(f"[sidecar] ping ✓ python={ping['result'].get('python')}")

        listed = call(2, "list_examples", {})
        total = listed.get("result", {}).get("total")
        if total != EXPECTED_EXAMPLES:
            raise SystemExit(f"[sidecar] list_examples 异常: total={total}（期望 {EXPECTED_EXAMPLES}）")
        print(f"[sidecar] list_examples ✓ total={total}")
        print("[sidecar] 冻结产物冒烟通过")
    except SystemExit as exc:
        # 失败即现场：退出码 + sidecar stderr 尾部（Windows 上的 traceback 只在这里看得见）
        print(f"[sidecar] 冒烟失败：{exc}")
        tail = err_log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-40:]
        for line in tail:
            print(f"[sidecar stderr] {line}")
        raise
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        err_file.close()
        shutil.rmtree(data_dir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="冻结并验证 Python sidecar")
    ap.add_argument("--smoke", action="store_true", help="冻结后启动产物做端到端冒烟")
    ap.add_argument("--clean", action="store_true", help="先清掉旧的产物与工作目录")
    args = ap.parse_args(argv)

    if args.clean:
        shutil.rmtree(OUT_DIR, ignore_errors=True)
        shutil.rmtree(ELECTRON_DIR / "build-pyinstaller" / "work", ignore_errors=True)
    binary = build()
    if args.smoke:
        smoke(binary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
