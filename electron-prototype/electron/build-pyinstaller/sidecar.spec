# -*- mode: python ; coding: utf-8 -*-
"""sidecar 冻结配置（PyInstaller；由 scripts/build_sidecar.py 调用）。

hiddenimports 由仓库里的 app/*.py 扫描生成，而不是手写清单：
B2 新增了 contract_store / facts / migration 等模块，手写清单漏项时
冻结产物会以 "ModuleNotFoundError" 在用户机器上才炸——扫描生成从根上避免这类漏配。
"""

import sys
from pathlib import Path

REPO = Path(SPECPATH).resolve().parents[2]  # PyCase/（spec 在 electron-prototype/electron/build-pyinstaller/）
APP_MODULES = sorted(
    f"app.{p.stem}" for p in (REPO / "app").glob("*.py") if p.stem != "__init__"
)

a = Analysis(
    [str(REPO / "electron-prototype" / "sidecar" / "server.py")],
    pathex=[str(REPO)],
    binaries=[],
    datas=[],
    hiddenimports=APP_MODULES,  # app 是命名空间包（无 __init__.py），必须显式点名
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # upx 压缩过的二进制在 macOS 上会被 Gatekeeper 判定异常；体积换可启动性
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
