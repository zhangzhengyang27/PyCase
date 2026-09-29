"""打包链不变量（B3-4）：不跑打包也能挡住"产物缺料"这一类缺陷。

为什么需要：打包验证在 CI 里要冻结 sidecar + 出包（分钟级），而最容易断的其实是
**静态配置**——extraResources 漏目录、sidecar 产物名与平台不符、冻结清单漏模块。
2026-09-29 打包冒烟就抓到过一次：31 条目录型示例的源码在 examples_assets/ 下，
extraResources 没带它 → 打包态主题分区少算 31 条。这里把那些配置事实钉成断言。
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ELECTRON_DIR = ROOT / "electron-prototype" / "electron"
PACKAGE_JSON = ELECTRON_DIR / "package.json"
SPEC = ELECTRON_DIR / "build-pyinstaller" / "sidecar.spec"
BUILD_SCRIPT = ROOT / "scripts" / "build_sidecar.py"


def _build_config() -> dict:
    return json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["build"]


def _shipped_trees() -> set[str]:
    """随包分发的资源顶层名（extraResources 的 to 值，如 json_examples / topics）。"""
    return {str(entry["to"]).split("/")[0] for entry in _build_config().get("extraResources", [])}


def test_packaging_ships_every_tree_the_manifests_reference():
    """清单里 file 指向的每一个顶层目录，都必须随包分发（否则条目在打包态缺料）。"""
    shipped = _shipped_trees()
    referenced: set[str] = set()
    for manifest in sorted((ROOT / "json_examples").glob("*.json")):
        if manifest.name == "facts.json":
            continue
        for entry in json.loads(manifest.read_text(encoding="utf-8"))["examples"]:
            file_rel = entry.get("file")
            if not file_rel:
                continue
            if file_rel.startswith("../"):  # 原位引用：../topics/x.py → 顶层树 topics
                referenced.add(file_rel.split("/")[1])
            else:  # 集合内相对路径（bulk_basics/x.py）→ 由 json_examples 一并携带
                referenced.add("json_examples")
    missing = referenced - shipped
    assert not missing, f"清单引用了未随包分发的目录树: {sorted(missing)}"


def test_packaging_platform_blocks_are_explicit():
    """mac/win 两块都要显式列 extraResources（平台块整体覆盖顶层同名键）。

    Windows 的 sidecar 产物是 sidecar.exe：平台块里必须指向 .exe，否则打包时找不到文件。
    """
    build = _build_config()
    for platform, expected in (("mac", "sidecar-dist/sidecar"), ("win", "sidecar-dist/sidecar.exe")):
        block = build.get(platform) or {}
        sources = [entry["from"] for entry in block.get("extraResources", [])]
        assert expected in sources, f"{platform} 块缺少 sidecar 产物: {expected}"
        assert "../../json_examples" in sources, f"{platform} 块缺少示例数据目录"
        assert "../../examples_assets" in sources, f"{platform} 块缺少 examples_assets（目录型示例源码）"


def test_sidecar_freeze_covers_all_app_modules():
    """冻结清单由 app/*.py 扫描生成——不能退回手写清单（B2 新增模块曾漏配）。"""
    spec = SPEC.read_text(encoding="utf-8")
    assert 'glob("*.py")' in spec, "spec 必须扫描 app/*.py 生成 hiddenimports"
    assert "hiddenimports=APP_MODULES" in spec
    # app 包下的模块一个都不能少（扫描口径本身也要对）
    modules = {p.stem for p in (ROOT / "app").glob("*.py") if p.stem != "__init__"}
    assert {"contract_store", "facts", "migration", "importer", "models", "venv_manager"} <= modules


def test_sidecar_build_entry_is_wired():
    """构建入口存在且与 spec / 产物目录约定一致（打包脚本即 CI 与 `npm run sidecar` 的实现）。"""
    script = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "build-pyinstaller" in script and "sidecar.spec" in script
    assert "sidecar-dist" in script
    assert "sidecar.exe" in script  # 平台产物名
    # 冻结产物名必须与 package.json 的 extraResources 约定同名
    assert '"sidecar.exe" if sys.platform == "win32" else "sidecar"' in script


def test_package_json_version_matches_version_file():
    """版本号单一来源：package.json 与仓库根 VERSION 一致（CI 另有 sync_version 门禁）。"""
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["version"] == version


def test_dist_artifacts_are_gitignored():
    """打包产物（dist / sidecar-dist）不得进仓库。"""
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "electron-prototype/electron/dist/" in ignored
    assert "electron-prototype/electron/sidecar-dist/" in ignored


def test_no_stale_default_icon_assumption():
    """图标现状如实记录：当前用 Electron 默认图标（品牌图标待 M6），别让文案假装有。"""
    build = _build_config()
    for platform in ("mac", "win"):
        block = build.get(platform) or {}
        assert "icon" not in block, "新增图标时请同步更新本断言与 docs/release.md"
    assert re.search(r"icon", json.dumps(build, ensure_ascii=False)) is None
