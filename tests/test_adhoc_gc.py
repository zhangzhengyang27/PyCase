"""adhoc 工作区 TTL 回收单元测试（contract_store._collect_adhoc_workspaces）。

背景：交互工具抽屉的每次「运行」都会在 workspace_root/adhoc/<run_id>/ 落一个
一次性目录（Task 7 契约）。这些目录没有账本，_has_user_assets 把 main.py 当
用户资产保守保留，默认 clean 永不回收——所以 collect_garbage 里补了按 mtime
的 TTL 扫除规则（图片预览的 file:// URL 只在运行会话内有效）。
"""

import os
import time
from pathlib import Path

from app.contract_store import ContractStore


def _store(tmp_path: Path) -> ContractStore:
    return ContractStore(
        collection_dir=tmp_path / "json_examples",
        data_root=tmp_path / "data",
        workspace_root=tmp_path / "cache",
        user_dir=tmp_path / "user",
        history_root=tmp_path / "edit_history",
    )


def test_stale_adhoc_dirs_removed_fresh_kept(tmp_path):
    store = _store(tmp_path)
    adhoc = store.workspace_root / "adhoc"
    old = adhoc / "run_old"
    fresh = adhoc / "run_fresh"
    old.mkdir(parents=True)
    fresh.mkdir(parents=True)
    (old / "main.py").write_text("print(1)", encoding="utf-8")
    (fresh / "main.py").write_text("print(2)", encoding="utf-8")
    # 把 old 的 mtime 拨到 TTL 之外
    stale = time.time() - (ContractStore.ADHOC_TTL_HOURS + 1) * 3600
    os.utime(old, (stale, stale))

    removed = store.collect_garbage()

    assert removed >= 1
    assert not old.exists()
    assert fresh.exists()


def test_fresh_adhoc_dirs_all_kept(tmp_path):
    store = _store(tmp_path)
    adhoc = store.workspace_root / "adhoc"
    for rid in ("r1", "r2"):
        (adhoc / rid).mkdir(parents=True)
        (adhoc / rid / "main.py").write_text("print(1)", encoding="utf-8")

    assert store.collect_garbage() == 0
    assert (adhoc / "r1").exists() and (adhoc / "r2").exists()


def test_no_adhoc_dir_is_noop(tmp_path):
    store = _store(tmp_path)
    assert store.collect_garbage() == 0
