"""重设计护栏测试 G1–G3：数据真相源 / 原子写 / 安全判定三态。

护栏的用法：B2–B3 全量重构期间冻结这些行为契约。
- 在旧实现上先绿（含 xfail 标注的目标行为）；
- 重构若破坏契约，护栏必须变红；
- 目标行为落地后 xfail 会转为 XPASS，strict 模式直接判失败，提醒摘除标记。

契约 v2 再表达（docs/redesign-data-contract.md §7）：断言事实不变（内容等价、自愈、
同步、原子、三态），只迁移观测点/时序——
- load 不再物化（零写盘），运行落盘一律经 ``store.ensure_workspace``；
- 保存写**真实文件**（不再回写清单内联 code；v1 兼容期只读）；
- 工作区替代旧"缓存目录"（``store.workspace_root``，``item.path`` 为真实/计划路径）。

对应 docs/redesign-plan.md 的 G1（真相源金标）、G2（原子写）、G3（安全三态/不 fail-open）。
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from app.contract_store import ContractStore
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
    """伪造仓库根标记目录，让 store 把 tmp_path 认作集合树根。"""
    for d in ("topics", "tools", "projects"):
        (tmp_path / d).mkdir()


def _write_collection(tmp_path: Path, name: str, examples: list[dict], *, user: bool = False) -> Path:
    coll = tmp_path / ("user_examples" if user else "json_examples")
    coll.mkdir(exist_ok=True)
    path = coll / f"{name}.json"
    path.write_text(json.dumps({"name": name, "examples": examples}, ensure_ascii=False), encoding="utf-8")
    return path


def _write_v2_collection(tmp_path: Path, name: str, examples: list[dict], *, user: bool = False) -> Path:
    """v2 夹具：把内联 code 落成真实文件并写 file 字段（契约 §2.2）。

    G2 断言的是"编辑真实文件"的原子性，必须用已迁移形态的清单：条目里的 code
    只是夹具输入，落盘后真实文件才是真相源。
    """
    coll = tmp_path / ("user_examples" if user else "json_examples")
    coll.mkdir(exist_ok=True)
    src_dir = coll / name
    src_dir.mkdir(exist_ok=True)
    entries: list[dict] = []
    for ex in examples:
        spec = dict(ex)
        code = spec.pop("code")
        (src_dir / spec["name"]).write_text(code, encoding="utf-8")
        spec["file"] = f"{name}/{spec['name']}"
        entries.append(spec)
    path = coll / f"{name}.json"
    path.write_text(
        json.dumps({"schema_version": 2, "name": name, "examples": entries}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _workspace_snapshot(store: ContractStore) -> tuple[bool, frozenset[str]]:
    """工作区根快照（是否存在 + 文件集合），load 前后比对断言"零写盘"（契约 §3.1）。"""
    root = store.workspace_root
    if not root.is_dir():
        return (False, frozenset())
    return (True, frozenset(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()))


# --------------------------------------------------------------------- G1 真相源金标


def test_g1_dataset_index_golden():
    """全量真相源金标（冻结基线 2026-09-29）：14 个集合 / 1496 条示例。

    数字是刻意写死的：重构期间真相源规模不得漂移；确需增删示例时连同本基线一起更新。
    v2 观测点：load = 只读清单 + 真实树建索引（**零写盘**，契约 §3.1）；源码按需
    ``store.get_code`` 取（v1 兼容期读清单内联 code，迁移后读真实文件）。
    """
    store = ContractStore.for_base_dir(base_dir=REPO_ROOT)
    assert len(sorted(store.collection_dir.glob("*.json"))) == 14
    before = _workspace_snapshot(store)  # 启动前的工作区现状
    items = _flat(store.load())
    assert _workspace_snapshot(store) == before, "load 必须零写盘（契约 §3.1）"
    assert len(items) == 1496
    # 内容等价：全部条目的源码都能按需取到（取不到即真相源内容缺失）
    missing = [i.json_id for i in items.values() if not store.get_code(i).strip()]
    assert missing == []
    # v2 形态的条目（清单带 file）直接对真实树断言：文件存在且与取到的源码逐字节一致
    mismatched = [
        i.json_id
        for i in items.values()
        if i.path.is_file() and i.path.read_text(encoding="utf-8") != store.get_code(i)
    ]
    assert mismatched == []


def test_g1_dir_example_materializes_siblings_and_run_path(tmp_path):
    """目录型示例：兄弟数据/模块随工作区到位；run_pythonpath 含工作区目录。

    v2：load 不再物化，``ensure_workspace`` 是唯一落盘入口（契约 §4.1）。
    """
    _make_root(tmp_path)
    src = tmp_path / "topics" / "demo"
    src.mkdir(parents=True)
    (src / "data.txt").write_text("payload-v1", encoding="utf-8")
    (src / "helper.py").write_text("VALUE = 42\n", encoding="utf-8")
    code = "import helper\n\nprint(helper.VALUE, open('data.txt').read())\n"
    _write_collection(tmp_path, "demo", [{"id": "demo_1", "name": "main.py", "code": code, "dir": "topics/demo"}])

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["demo_1"]
    assert not item.path.is_file()  # load 零写盘：工作区/真实文件都还没落

    workspace = store.ensure_workspace(item)
    assert workspace is not None
    # 目标文件基线（v1 兼容期来自清单内联 code；迁移后来自真实文件）
    assert (workspace / "main.py").read_text(encoding="utf-8") == code
    assert (workspace / "data.txt").read_text(encoding="utf-8") == "payload-v1"
    assert (workspace / "helper.py").read_text(encoding="utf-8") == "VALUE = 42\n"
    assert str(workspace) in store.run_pythonpath(item)  # 运行路径含工作区（兄弟/包导入）


def test_g1_cache_self_heal_after_delete(tmp_path):
    """工作区整体删除后重建应自愈（工作区是可再生的派生数据，契约 §4.4）。"""
    _make_root(tmp_path)
    src = tmp_path / "tools" / "crawler"
    src.mkdir(parents=True)
    (src / "seed.txt").write_text("seeds", encoding="utf-8")
    _write_collection(tmp_path, "tools", [{"id": "t1", "name": "main.py", "code": "print(1)\n", "dir": "tools/crawler"}])

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["t1"]
    workspace = store.ensure_workspace(item)
    assert workspace is not None and (workspace / "main.py").is_file()  # 首次落盘已发生
    shutil.rmtree(store.workspace_root)

    item2 = _flat(store.load())["t1"]
    workspace2 = store.ensure_workspace(item2)
    assert workspace2 is not None
    assert (workspace2 / "main.py").read_text(encoding="utf-8") == "print(1)\n"
    assert (workspace2 / "seed.txt").read_text(encoding="utf-8") == "seeds"


def test_g1_new_source_file_syncs_even_if_cache_newer(tmp_path):
    """源目录后补文件必须同步到工作区——哪怕工作区 mtime 比源目录更新。

    落基线会往工作区写 .py（把工作区 mtime 顶得比源新）；若用 mtime 新旧判断
    是否重拷，源目录后补的兄弟模块/数据文件将永远无法同步（v2 按内容哈希做差集）。
    """
    _make_root(tmp_path)
    src = tmp_path / "topics" / "late"
    src.mkdir(parents=True)
    (src / "base.txt").write_text("base", encoding="utf-8")
    _write_collection(tmp_path, "late", [{"id": "l1", "name": "main.py", "code": "print(1)\n", "dir": "topics/late"}])

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["l1"]
    workspace = store.ensure_workspace(item)  # 首次落基线：工作区 mtime 被顶到源之后
    assert workspace is not None
    assert workspace.stat().st_mtime > src.stat().st_mtime

    # 后补文件并复原时间戳：任何"比谁新"的启发式都看不到这次变化
    before = src.stat().st_mtime
    (src / "late.txt").write_text("late-data", encoding="utf-8")
    os.utime(src / "late.txt", (before, before))
    os.utime(src, (before, before))

    item2 = _flat(store.load())["l1"]
    workspace2 = store.ensure_workspace(item2)
    assert workspace2 is not None
    assert (workspace2 / "late.txt").read_text(encoding="utf-8") == "late-data"


def test_g1_source_file_change_triggers_recopy(tmp_path):
    """源目录既存文件内容变化后再次 ensure_workspace 必须重拷（工作区里是旧内容即算回归）。"""
    _make_root(tmp_path)
    src = tmp_path / "topics" / "edit"
    src.mkdir(parents=True)
    (src / "data.txt").write_text("v1", encoding="utf-8")
    _write_collection(tmp_path, "edit", [{"id": "e1", "name": "main.py", "code": "print(1)\n", "dir": "topics/edit"}])

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["e1"]
    assert store.ensure_workspace(item) is not None
    (src / "data.txt").write_text("v2-changed", encoding="utf-8")

    item2 = _flat(store.load())["e1"]
    workspace = store.ensure_workspace(item2)
    assert workspace is not None
    assert (workspace / "data.txt").read_text(encoding="utf-8") == "v2-changed"


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
    """保存中途失败必须逐字节完好——真实文件不被截断、清单不被改动、不留 .tmp。

    v2 观测点：编辑原子写**真实文件**（不再回写清单内联 code，契约 §2.2/§7）。
    """
    _make_root(tmp_path)
    examples = [{"id": f"ex{i}", "name": f"ex{i}.py", "code": f"print({i})\n"} for i in range(30)]
    json_file = _write_v2_collection(tmp_path, "bulk", examples)
    manifest_before = json_file.read_text(encoding="utf-8")

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["ex7"]
    target = item.path
    code_before = target.read_text(encoding="utf-8")

    monkeypatch.setattr(Path, "write_text", _flaky_write_text_once(target.parent))
    try:
        assert store.save_item(item, "print('changed')\n") is False
    finally:
        monkeypatch.undo()

    assert target.read_text(encoding="utf-8") == code_before
    assert json_file.read_text(encoding="utf-8") == manifest_before
    assert list(target.parent.glob("*.tmp")) == []


def test_g2_delete_survives_midwrite_failure(tmp_path, monkeypatch):
    """删除用户示例的中途失败不得截断清单，也不得留下"删了一半"的状态。

    v2 删除 = 清单条目 + 真实文件 + 工作区三处清理（契约 §5）；清单写失败时
    真实文件必须原样在位（本次删除整体未生效）。
    """
    _make_root(tmp_path)
    examples = [
        {"id": "u1", "name": "u1.py", "code": "print(1)\n"},
        {"id": "u2", "name": "u2.py", "code": "print(2)\n"},
    ]
    json_file = _write_v2_collection(tmp_path, "mine", examples, user=True)
    before = json_file.read_text(encoding="utf-8")

    store = ContractStore.for_base_dir(base_dir=tmp_path, user_dir=tmp_path / "user_examples")
    item = _flat(store.load())["u1"]
    target = item.path

    monkeypatch.setattr(Path, "write_text", _flaky_write_text_once(json_file.parent))
    try:
        assert store.delete_user_example(item) is False
    finally:
        monkeypatch.undo()

    assert json_file.read_text(encoding="utf-8") == before
    assert target.read_text(encoding="utf-8") == "print(1)\n"
    assert list(json_file.parent.glob("*.tmp")) == []


def test_g2_save_updates_only_target_and_leaves_no_tmp(tmp_path):
    """成功保存：只改目标真实文件、同集合其他示例文件不变、清单不动、工作区同步、无 .tmp 残留。"""
    _make_root(tmp_path)
    examples = [
        {"id": "s1", "name": "s1.py", "code": "print(1)\n"},
        {"id": "s2", "name": "s2.py", "code": "print(2)\n"},
        {"id": "s3", "name": "s3.py", "code": "print(3)\n"},
    ]
    json_file = _write_v2_collection(tmp_path, "three", examples)
    manifest_before = json_file.read_text(encoding="utf-8")

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["s2"]
    workspace = store.ensure_workspace(item)
    assert workspace is not None and store.save_item(item, "print(22)\n") is True

    assert item.path.read_text(encoding="utf-8") == "print(22)\n"
    siblings = [p.read_text(encoding="utf-8") for p in sorted(item.path.parent.glob("*.py"))]
    assert siblings == ["print(1)\n", "print(22)\n", "print(3)\n"]
    assert (workspace / "s2.py").read_text(encoding="utf-8") == "print(22)\n"  # 工作区基线同步
    assert json_file.read_text(encoding="utf-8") == manifest_before  # 清单是元数据，保存不碰它
    assert list(item.path.parent.glob("*.tmp")) == []


# ------------------------------------------------------ G3 安全三态 / 不 fail-open

_CLEAN_CODE = "def add(a, b):\n    return a + b\n\n\nprint(add(1, 2))\n"
_HIGH_RISK_CODE = "import shutil\n\nshutil.rmtree('/tmp/pycase-guard-demo')\n"
_BROKEN_CODE = "def f(:\n    pass\n"
_EMPTY_CODE = '"""只有一个 docstring。"""\n'


def _status_store(tmp_path: Path) -> ContractStore:
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
    return ContractStore.for_base_dir(base_dir=tmp_path)


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
