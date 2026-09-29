#!/usr/bin/env python3
"""版本号单一来源工具（VERSION 为唯一真相源）。

写入位置（每个都是"曾经手写、互相漂移过"的地方）：
- ``electron-prototype/electron/package.json`` 的 ``version``（运行时唯一读取点：app.getVersion()）
- ``pyproject.toml`` 的 ``version``
- ``app/_version.py``（sidecar 自报版本，PyInstaller 冻结后也能读）

用法：
    python scripts/sync_version.py            # 按 VERSION 同步全部位置
    python scripts/sync_version.py --check    # CI 门禁：任一位置与 VERSION 不一致即退出 1
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"
PACKAGE_JSON = ROOT / "electron-prototype" / "electron" / "package.json"
PYPROJECT = ROOT / "pyproject.toml"
PY_VERSION = ROOT / "app" / "_version.py"

_HEADER = '"""应用版本（唯一来源 = 仓库根 VERSION；由 python scripts/sync_version.py 生成，勿手改）。"""\n'


def read_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+([-.][0-9A-Za-z.]+)?", text):
        raise SystemExit(f"VERSION 内容不合法: {text!r}")
    return text


def _render_py(version: str) -> str:
    return f'{_HEADER}\n__version__ = "{version}"\n'


def _render_pyproject(text: str, version: str) -> str:
    new = re.sub(r'(?m)^version = "[^"]*"', f'version = "{version}"', text, count=1)
    if new == text and f'version = "{version}"' not in text:
        raise SystemExit("pyproject.toml 未找到 version = ... 行")
    return new


def planned(version: str) -> dict[Path, str]:
    """各位置的期望内容（package.json 用 json 往返，保持既有缩进/键序）。"""
    pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    pkg["version"] = version
    return {
        PACKAGE_JSON: json.dumps(pkg, ensure_ascii=False, indent=2) + "\n",
        PYPROJECT: _render_pyproject(PYPROJECT.read_text(encoding="utf-8"), version),
        PY_VERSION: _render_py(version),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="版本号单一来源同步/校验")
    ap.add_argument("--check", action="store_true", help="只校验不写盘（CI 用）")
    args = ap.parse_args(argv)

    version = read_version()
    written: list[str] = []
    stale: list[str] = []
    for path, expected in planned(version).items():
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current == expected:
            continue
        if args.check:
            stale.append(str(path.relative_to(ROOT)))
            continue
        path.write_text(expected, encoding="utf-8")
        written.append(str(path.relative_to(ROOT)))

    if args.check:
        if stale:
            print(f"[version] 与 VERSION({version}) 不一致：{', '.join(stale)}；跑 python scripts/sync_version.py", file=sys.stderr)
            return 1
        print(f"[version] 一致：{version}")
        return 0
    print(f"[version] {version} → {'、'.join(written) if written else '无变化'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
