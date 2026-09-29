"""重设计护栏 G5b/G6b：工作区治理（契约 §4.4：上限 / 清理 / 孤儿回收 / 资产保全）。

工作区是运行时唯一的落盘入口，治理动作必须"删得准、留得住"：
- 上限（1GiB + LRU）：超限先淘汰最久未用的**干净**条目；
- 清理：只在没有干净候选时才动含用户资产的条目，且必须有日志；
- 孤儿回收：不在索引键集合里的工作区可回收，但**不得静默删掉用户资产**；
- 资产保全：基线文件随刷新更新，用户资产与运行产物永不随刷新丢失。

全部在 tmp 沙箱内跑，不碰仓库真相源与真实缓存。
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.contract_store import ContractStore  # noqa: E402


def _store(tmp_path: Path, examples: list[dict]) -> ContractStore:
    """构造 v2 集合的 store（清单 + 真实文件同根，工作区在 tmp 内）。"""
    for d in ("topics", "tools", "projects"):
        (tmp_path / d).mkdir(exist_ok=True)
    coll = tmp_path / "json_examples"
    src = coll / "demo"
    src.mkdir(parents=True)
    entries = []
    for ex in examples:
        spec = dict(ex)
        code = spec.pop("code")
        (src / spec["name"]).write_text(code, encoding="utf-8")
        spec["file"] = f"demo/{spec['name']}"
        entries.append(spec)
    (coll / "demo.json").write_text(
        json.dumps({"schema_version": 2, "name": "demo", "examples": entries}, ensure_ascii=False),
        encoding="utf-8",
    )
    store = ContractStore.for_base_dir(base_dir=tmp_path)
    store.load()
    return store


def _materialize(store: ContractStore, example_id: str, payload: bytes = b"x" * 1000) -> Path:
    """确保工作区就绪并塞入一个运行产物（不进账本 → 算用户资产）。"""
    item = store.index[example_id]
    workspace = store.ensure_workspace(item)
    assert workspace is not None
    (workspace / "output.bin").write_bytes(payload)
    return workspace


def test_workspace_usage_counts_files(tmp_path):
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    _materialize(store, "a", b"x" * 512)
    usage = store.workspace_usage()
    assert usage >= 512
    assert usage == sum(p.stat().st_size for p in store.workspace_root.rglob("*") if p.is_file())


def test_prune_evicts_oldest_clean_first(tmp_path):
    """超限先淘汰最久未用的干净条目；含用户资产的条目在还有干净候选时不动。"""
    store = _store(
        tmp_path,
        [
            {"id": "old", "name": "old.py", "code": "print(1)\n"},
            {"id": "new", "name": "new.py", "code": "print(2)\n"},
        ],
    )
    old_ws = _materialize(store, "old", b"a" * 2000)
    # old 是干净条目（无资产），new 有用户资产
    old_ws.joinpath("output.bin").unlink()
    new_ws = _materialize(store, "new", b"b" * 2000)
    old_size = sum(p.stat().st_size for p in old_ws.rglob("*") if p.is_file())
    # 拉开 last_used：old 更久未用
    past = time.time() - 3600
    for p in (old_ws / ".manifest.json", old_ws):
        if p.exists():
            import os

            os.utime(p, (past, past))

    removed = store.prune(max_bytes=store.workspace_usage() - old_size)
    assert removed == 1
    assert not old_ws.exists(), "最久未用的干净条目应先被淘汰"
    assert new_ws.exists(), "含用户资产的条目在还有干净候选时不得被淘汰"


def test_prune_evicts_assets_only_as_last_resort(tmp_path):
    """仍超限且无干净候选时才淘汰含资产的条目（契约 §4.4）。"""
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    ws = _materialize(store, "a", b"c" * 4000)
    removed = store.prune(max_bytes=1000)
    assert removed == 1
    assert not ws.exists()


def test_garbage_collection_removes_orphans(tmp_path):
    """孤儿工作区（不在索引键集合内）可回收。"""
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    alive = _materialize(store, "a")
    orphan = store.workspace_root / "ghost-12345678"
    orphan.mkdir(parents=True)
    (orphan / ".manifest.json").write_text(json.dumps({"files": {}}), encoding="utf-8")

    removed = store.collect_garbage()
    assert removed == 1
    assert not orphan.exists()
    assert alive.exists(), "在册条目的工作区不得被回收"


def test_garbage_collection_keeps_orphan_with_user_assets(tmp_path):
    """孤儿里若含用户资产，不得静默删除（留给手动清理；契约 §4.4）。"""
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    _materialize(store, "a")
    orphan = store.workspace_root / "ghost-87654321"
    orphan.mkdir(parents=True)
    (orphan / ".manifest.json").write_text(json.dumps({"files": {"a.py": "deadbeef"}}), encoding="utf-8")
    (orphan / "user_upload.png").write_bytes(b"\x89PNG")

    removed = store.collect_garbage()
    assert removed == 0
    assert (orphan / "user_upload.png").is_file(), "孤儿回收删掉了用户资产"


def test_user_assets_excludes_baseline_and_ledger(tmp_path):
    """资产面板口径：工作区里不在账本中的文件才是用户资产。"""
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    ws = _materialize(store, "a")
    assets = {p.name for p in store.user_assets(store.index["a"])}
    assert "output.bin" in assets
    assert "a.py" not in assets, "基线文件不算用户资产"
    assert ".manifest.json" not in assets, "工作区账本不算用户资产"
    assert (ws / "a.py").is_file()


def test_workspace_refresh_preserves_user_assets(tmp_path):
    """基线刷新（真实文件改了）只更新基线文件，用户资产与运行产物原地保留。"""
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    ws = _materialize(store, "a")
    # 两次刷新之间加入用户资产，并改真实文件触发基线刷新
    (tmp_path / "json_examples" / "demo" / "a.py").write_text("print(2)\n", encoding="utf-8")
    item = store.index["a"]
    store.ensure_workspace(item)
    assert (ws / "a.py").read_text(encoding="utf-8") == "print(2)\n"
    assert (ws / "output.bin").is_file(), "基线刷新删掉了运行产物"


# ----------------------------------------------- 编辑历史（A6 可恢复编辑）


def _edit_store(tmp_path: Path) -> ContractStore:
    store = _store(tmp_path, [{"id": "a", "name": "a.py", "code": "print(1)\n"}])
    store.history_root = tmp_path / "edit_history"
    return store


def test_edit_history_snapshot_and_restore(tmp_path):
    """保存覆盖前留快照；可查看历史内容并一键还原（还原本身也可回退）。"""
    store = _edit_store(tmp_path)
    item = store.index["a"]
    assert store.save_item(item, "print(2)\n") is True

    versions = store.list_versions(item)
    assert len(versions) == 1, "保存应留下旧内容快照"
    old = store.read_version(item, versions[0]["ts"])
    assert old == "print(1)\n"

    # 还原：当前内容（print(2)）也留一份快照，可再回退
    assert store.restore_version(item, versions[0]["ts"]) is True
    assert item.path.read_text(encoding="utf-8") == "print(1)\n"
    assert store.read_version(item, versions[0]["ts"]) == "print(1)\n"
    assert len(store.list_versions(item)) == 2, "还原前应给当时内容留快照"


def test_edit_history_keeps_recent_versions_only(tmp_path):
    """历史保留最近 10 版，旧快照自动裁剪。"""
    store = _edit_store(tmp_path)
    item = store.index["a"]
    for i in range(2, 14):  # 12 次保存 → 12 份快照
        assert store.save_item(item, f"print({i})\n") is True
        time.sleep(0.01)
    versions = store.list_versions(item)
    assert len(versions) == ContractStore.VERSION_KEEP
    # 最新一份应是倒数第二次保存的内容
    assert store.read_version(item, versions[0]["ts"]) == "print(12)\n"


def test_read_version_rejects_path_traversal(tmp_path):
    store = _edit_store(tmp_path)
    item = store.index["a"]
    store.save_item(item, "print(2)\n")
    assert store.read_version(item, "../secrets") is None
    assert store.read_version(item, "") is None


# ----------------------------------------------- 存储治理（A6 缓存入口）


def test_storage_report_lists_workspace_and_legacy(tmp_path):
    store = _edit_store(tmp_path)
    item = store.index["a"]
    ws = store.ensure_workspace(item)
    assert ws is not None
    (ws / "output.bin").write_bytes(b"x" * 300)
    # 造一个 v1 旧根残留（缓存根下非 v2 的目录）
    legacy = store.cache_root / "old_example-1234abcd"
    legacy.mkdir(parents=True)
    (legacy / "a.py").write_bytes(b"y" * 500)

    report = store.storage_report()
    assert report["workspace"]["bytes"] >= 300
    assert report["workspace"]["max_bytes"] > 0
    assert [e["key"] for e in report["workspace"]["entries"]] == [ws.name]
    assert report["workspace"]["entries"][0]["has_assets"] is True
    assert report["workspace"]["asset_entries"] == 1
    assert report["legacy"]["entries"] == 1
    assert report["legacy"]["bytes"] >= 500


def test_clean_workspace_two_modes(tmp_path):
    """clean 保留含用户资产的条目；all 全清（用户显式选择）。"""
    store = _edit_store(tmp_path)
    item = store.index["a"]
    with_asset = store.ensure_workspace(item)
    assert with_asset is not None
    (with_asset / "keep.bin").write_bytes(b"z" * 100)

    result = store.clean_workspace("clean")
    assert result["removed"] == 0 and result["kept"] == 1
    assert with_asset.is_dir(), "clean 模式不得删除含用户资产的工作区"

    result = store.clean_workspace("all")
    assert result["removed"] == 1 and result["freed_bytes"] >= 100
    assert not with_asset.exists()


def test_reclaim_legacy_cache_keeps_v2(tmp_path):
    """v1 旧根回收只清缓存根下非 v2 的内容，工作区与烘焙事实不受影响。"""
    store = _edit_store(tmp_path)
    item = store.index["a"]
    ws = store.ensure_workspace(item)
    assert ws is not None
    facts = store.workspace_root / "facts.json"
    facts.write_text("{}", encoding="utf-8")
    legacy_dir = store.cache_root / "v1_stale-dir"
    legacy_dir.mkdir()
    (legacy_dir / "a.py").write_bytes(b"q" * 200)
    legacy_file = store.cache_root / "stray.tmp"
    legacy_file.write_bytes(b"t" * 10)

    result = store.reclaim_legacy_cache()
    assert result["removed"] == 2
    assert not legacy_dir.exists() and not legacy_file.exists()
    assert ws.is_dir(), "回收旧根不得触碰 v2 工作区"
    assert facts.is_file(), "回收旧根不得删掉烘焙事实缓存"


def test_clean_workspace_rejects_unknown_mode(tmp_path):
    store = _edit_store(tmp_path)
    try:
        store.clean_workspace("nuke")
    except ValueError as e:
        assert "nuke" in str(e)
    else:  # pragma: no cover - 明确失败路径
        raise AssertionError("未知模式必须拒绝")
