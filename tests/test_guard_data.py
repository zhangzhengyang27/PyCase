"""重设计护栏测试 G1–G3：数据真相源 / 原子写 / 安全判定三态。

护栏的用法：B2–B3 全量重构期间冻结这些行为契约。
- 在旧实现上先绿（含 xfail 标注的目标行为）；
- 重构若破坏契约，护栏必须变红；
- 目标行为落地后 xfail 会转为 XPASS，strict 模式直接判失败，提醒摘除标记。

对应 docs/redesign-plan.md 的 G1（物化金标）、G2（原子写）、G3（安全三态/不 fail-open）。
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from app.json_examples import ExampleStore
from app.models import ExampleItem
from app.run_status import BROKEN, EMPTY, RISKY, RUNNABLE
from app.security import SecurityChecker

REPO_ROOT = Path(__file__).resolve().parent.parent

B2_TARGET = "B2 目标行为：旧实现尚未满足；一旦 XPASS 即表示已落地，应摘除 xfail 标记"


# --------------------------------------------------------------------- 公共工具


def _flat(root: ExampleItem) -> dict[str, ExampleItem]:
    """json_id -> ExampleItem 扁平索引。"""
    out: dict[str, ExampleItem] = {}

    def walk(item: ExampleItem) -> None:
        if not item.is_dir and item.json_id:
            out[item.json_id] = item
        for child in item.children:
            walk(child)

    walk(root)
    return out


def _make_root(tmp_path: Path) -> None:
    """伪造仓库根标记目录，让 ExampleStore._find_repo_root 把 tmp_path 认作根。"""
    for d in ("topics", "tools", "projects"):
        (tmp_path / d).mkdir()


def _write_collection(tmp_path: Path, name: str, examples: list[dict], *, user: bool = False) -> Path:
    coll = tmp_path / ("user_examples" if user else "json_examples")
    coll.mkdir(exist_ok=True)
    path = coll / f"{name}.json"
    path.write_text(json.dumps({"name": name, "examples": examples}, ensure_ascii=False), encoding="utf-8")
    return path


# --------------------------------------------------------------------- G1 物化金标


def test_g1_dataset_index_golden():
    """全量真相源金标（冻结基线 2026-09-29）：14 个集合 / 1496 条示例全量物化。

    数字是刻意写死的：重构期间真相源规模不得漂移；确需增删示例时连同本基线一起更新。
    """
    store = ExampleStore(base_dir=REPO_ROOT)
    assert len(sorted(store.collection_dir.glob("*.json"))) == 14
    items = _flat(store.load())
    assert len(items) == 1496
    # 全量物化成功：每条示例都有真实 .py，且与 JSON 中的代码逐字一致
    missing = [i.json_id for i in items.values() if not i.path.is_file()]
    assert missing == []
    mismatched = [i.json_id for i in items.values() if i.path.read_text(encoding="utf-8") != i.code]
    assert mismatched == []


def test_g1_dir_example_materializes_siblings_and_run_path(tmp_path):
    """目录型示例：兄弟数据/模块随目录物化；run_pythonpath 含原始目录与缓存目录。"""
    _make_root(tmp_path)
    src = tmp_path / "topics" / "demo"
    src.mkdir(parents=True)
    (src / "data.txt").write_text("payload-v1", encoding="utf-8")
    (src / "helper.py").write_text("VALUE = 42\n", encoding="utf-8")
    code = "import helper\n\nprint(helper.VALUE, open('data.txt').read())\n"
    _write_collection(tmp_path, "demo", [{"id": "demo_1", "name": "main.py", "code": code, "dir": "topics/demo"}])

    store = ExampleStore(base_dir=tmp_path)
    item = _flat(store.load())["demo_1"]

    assert item.path.read_text(encoding="utf-8") == code  # JSON 代码覆盖目标文件
    assert (item.path.parent / "data.txt").read_text(encoding="utf-8") == "payload-v1"
    assert (item.path.parent / "helper.py").read_text(encoding="utf-8") == "VALUE = 42\n"
    assert str(src) in item.run_pythonpath  # 原始目录（包/兄弟导入）
    assert str(item.path.parent) in item.run_pythonpath  # 物化缓存目录


def test_g1_cache_self_heal_after_delete(tmp_path):
    """缓存目录整体删除后重载应自愈重建（缓存是可再生的派生数据）。"""
    _make_root(tmp_path)
    src = tmp_path / "tools" / "crawler"
    src.mkdir(parents=True)
    (src / "seed.txt").write_text("seeds", encoding="utf-8")
    _write_collection(tmp_path, "tools", [{"id": "t1", "name": "main.py", "code": "print(1)\n", "dir": "tools/crawler"}])

    store = ExampleStore(base_dir=tmp_path)
    assert _flat(store.load())["t1"].path.is_file()  # 首次物化已发生
    shutil.rmtree(store.cache_dir)

    item2 = _flat(store.load())["t1"]
    assert item2.path.read_text(encoding="utf-8") == "print(1)\n"
    assert (item2.path.parent / "seed.txt").read_text(encoding="utf-8") == "seeds"


def test_g1_new_source_file_syncs_even_if_cache_newer(tmp_path):
    """源目录后补文件必须同步到缓存——哪怕缓存 mtime 比源目录更新。

    物化会往缓存写 .py（把缓存 mtime 顶得比源新）；若用 mtime 新旧判断
    是否重拷，源目录后补的兄弟模块/数据文件将永远无法同步。
    """
    _make_root(tmp_path)
    src = tmp_path / "topics" / "late"
    src.mkdir(parents=True)
    (src / "base.txt").write_text("base", encoding="utf-8")
    _write_collection(tmp_path, "late", [{"id": "l1", "name": "main.py", "code": "print(1)\n", "dir": "topics/late"}])

    store = ExampleStore(base_dir=tmp_path)
    _flat(store.load())  # 首次物化：缓存 mtime 被顶到源之后
    cache_dir = store.cache_dir / "topics_late"
    assert cache_dir.stat().st_mtime > src.stat().st_mtime

    # 后补文件并复原时间戳：任何"比谁新"的启发式都看不到这次变化
    before = src.stat().st_mtime
    (src / "late.txt").write_text("late-data", encoding="utf-8")
    os.utime(src / "late.txt", (before, before))
    os.utime(src, (before, before))

    item = _flat(store.load())["l1"]
    assert (item.path.parent / "late.txt").read_text(encoding="utf-8") == "late-data"


def test_g1_source_file_change_triggers_recopy(tmp_path):
    """源目录既存文件内容变化后重载必须重拷（缓存里是旧内容即算回归）。"""
    _make_root(tmp_path)
    src = tmp_path / "topics" / "edit"
    src.mkdir(parents=True)
    (src / "data.txt").write_text("v1", encoding="utf-8")
    _write_collection(tmp_path, "edit", [{"id": "e1", "name": "main.py", "code": "print(1)\n", "dir": "topics/edit"}])

    store = ExampleStore(base_dir=tmp_path)
    _flat(store.load())
    (src / "data.txt").write_text("v2-changed", encoding="utf-8")

    item = _flat(store.load())["e1"]
    assert (item.path.parent / "data.txt").read_text(encoding="utf-8") == "v2-changed"


# --------------------------------------------------------------------- G2 原子写


def _flaky_write_text_once(target_dir: Path):
    """返回一个 Path.write_text 替身：目录内首次写入先截断再抛错（模拟写盘中途故障）。"""
    real_write_text = Path.write_text
    state = {"failed": False}

    def flaky(self, data, **kwargs):
        if not state["failed"] and str(self).startswith(str(target_dir)):
            state["failed"] = True
            with open(self, "w", encoding="utf-8"):
                pass
            raise OSError("simulated mid-write failure")
        return real_write_text(self, data, **kwargs)

    return flaky


def test_g2_collection_survives_midwrite_failure(tmp_path, monkeypatch):
    """30 条示例的集合在回写中途失败时必须逐字节完好——不能截断、不能留 .tmp。"""
    _make_root(tmp_path)
    examples = [{"id": f"ex{i}", "name": f"ex{i}.py", "code": f"print({i})\n"} for i in range(30)]
    json_file = _write_collection(tmp_path, "bulk", examples)
    before = json_file.read_text(encoding="utf-8")

    store = ExampleStore(base_dir=tmp_path)
    item = _flat(store.load())["ex7"]

    monkeypatch.setattr(Path, "write_text", _flaky_write_text_once(json_file.parent))
    try:
        assert store.save_item(item, "print('changed')\n") is False
    finally:
        monkeypatch.undo()

    assert json_file.read_text(encoding="utf-8") == before
    assert list(json_file.parent.glob("*.tmp")) == []


def test_g2_delete_survives_midwrite_failure(tmp_path, monkeypatch):
    """删除用户示例的中途失败同样不得截断集合文件。"""
    _make_root(tmp_path)
    examples = [
        {"id": "u1", "name": "u1.py", "code": "print(1)\n"},
        {"id": "u2", "name": "u2.py", "code": "print(2)\n"},
    ]
    json_file = _write_collection(tmp_path, "mine", examples, user=True)
    before = json_file.read_text(encoding="utf-8")

    store = ExampleStore(base_dir=tmp_path, user_dir=tmp_path / "user_examples")
    item = _flat(store.load())["u1"]

    monkeypatch.setattr(Path, "write_text", _flaky_write_text_once(json_file.parent))
    try:
        assert store.delete_user_example(item) is False
    finally:
        monkeypatch.undo()

    assert json_file.read_text(encoding="utf-8") == before
    assert list(json_file.parent.glob("*.tmp")) == []


def test_g2_save_updates_only_target_and_leaves_no_tmp(tmp_path):
    """成功回写：只改目标示例、同集合其他示例不变、无 .tmp 残留、缓存同步。"""
    _make_root(tmp_path)
    examples = [
        {"id": "s1", "name": "s1.py", "code": "print(1)\n"},
        {"id": "s2", "name": "s2.py", "code": "print(2)\n"},
        {"id": "s3", "name": "s3.py", "code": "print(3)\n"},
    ]
    json_file = _write_collection(tmp_path, "three", examples)

    store = ExampleStore(base_dir=tmp_path)
    item = _flat(store.load())["s2"]
    assert store.save_item(item, "print(22)\n") is True

    data = json.loads(json_file.read_text(encoding="utf-8"))
    codes = {s["id"]: s["code"] for s in data["examples"]}
    assert codes == {"s1": "print(1)\n", "s2": "print(22)\n", "s3": "print(3)\n"}
    assert item.path.read_text(encoding="utf-8") == "print(22)\n"
    assert list(json_file.parent.glob("*.tmp")) == []


# ------------------------------------------------------ G3 安全三态 / 不 fail-open

_CLEAN_CODE = "def add(a, b):\n    return a + b\n\n\nprint(add(1, 2))\n"
_HIGH_RISK_CODE = "import shutil\n\nshutil.rmtree('/tmp/pycase-guard-demo')\n"
_BROKEN_CODE = "def f(:\n    pass\n"
_EMPTY_CODE = '"""只有一个 docstring。"""\n'


def _status_store(tmp_path: Path) -> ExampleStore:
    _make_root(tmp_path)
    _write_collection(
        tmp_path,
        "states",
        [
            {"id": "clean", "name": "clean.py", "code": _CLEAN_CODE},
            {"id": "risky", "name": "risky.py", "code": _HIGH_RISK_CODE},
            {"id": "broken", "name": "broken.py", "code": _BROKEN_CODE},
            {"id": "empty", "name": "empty.py", "code": _EMPTY_CODE},
        ],
    )
    return ExampleStore(base_dir=tmp_path)


def test_g3_status_five_state_golden(tmp_path):
    """干净/高危/坏语法/空壳分别判定为 runnable/risky/broken/empty。"""
    store = _status_store(tmp_path)
    items = _flat(store.load())
    assert store.ensure_run_status(items["clean"]) == RUNNABLE
    assert store.ensure_run_status(items["risky"]) == RISKY
    assert store.ensure_run_status(items["broken"]) == BROKEN
    assert store.ensure_run_status(items["empty"]) == EMPTY


def test_g3_high_risk_findings_for_confirm_dialog(tmp_path):
    """高危判定与其明细同源：运行前确认弹窗读到的必须是可解释的风险条目。"""
    store = _status_store(tmp_path)
    items = _flat(store.load())

    findings = store.ensure_risk_findings(items["risky"])
    assert findings and "删除" in findings[0]["description"]
    assert findings[0]["category"] == "file"
    assert store.ensure_risk_high(items["risky"]) is True

    assert store.ensure_risk_findings(items["clean"]) == []
    assert store.ensure_risk_high(items["clean"]) is False


@pytest.mark.xfail(strict=True, reason=B2_TARGET)
def test_g3_scanner_exception_must_not_fail_open(tmp_path, monkeypatch):
    """扫描器自身异常不得被吞成"可运行/无风险"（当前实现对内部异常 fail-open）。"""

    class _BoomChecker:
        def check(self, *args, **kwargs):
            raise RuntimeError("scanner crashed")

    store = _status_store(tmp_path)
    items = _flat(store.load())
    monkeypatch.setattr(store._scorer, "security_checker", _BoomChecker())

    assert store.ensure_run_status(items["clean"]) != RUNNABLE


@pytest.mark.xfail(strict=True, reason=B2_TARGET)
def test_g3_asyncio_run_is_not_subprocess(tmp_path):
    """asyncio.run() 不是子进程调用：不得按属性名 run 误报为 subprocess。"""
    code = "import asyncio\n\n\nasync def main():\n    return 1\n\n\nprint(asyncio.run(main()))\n"
    path = tmp_path / "async_demo.py"
    path.write_text(code, encoding="utf-8")

    report = SecurityChecker().check(path)
    assert not any("subprocess" in r for r in report.risks)
