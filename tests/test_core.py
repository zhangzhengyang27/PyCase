"""保留核心模块（Electron sidecar 复用链路）的单元测试，无需图形界面。

覆盖：仓库根识别、示例加载、物化（含兄弟数据文件）、JSON 回写、
安全扫描、质量评分、VenvManager 的 Python 解释器注入。
"""

import json
import os
import shutil
import sys
from pathlib import Path

import pytest
from app.contract_store import ContractStore
from app.models import ExampleItem
from app.quality import QualityScorer
from app.security import SecurityChecker
from app.venv_manager import VenvManager

APP_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def items() -> dict[str, ExampleItem]:
    """加载全部示例并构建 json_id -> ExampleItem 扁平索引。"""
    store = ContractStore.for_base_dir(base_dir=APP_DIR)
    root = store.load()
    flat: dict[str, ExampleItem] = {}

    def walk(item: ExampleItem) -> None:
        if not item.is_dir and item.json_id:
            flat[item.json_id] = item
        for child in item.children:
            walk(child)

    walk(root)
    return flat


def test_repo_root_is_project_itself():
    """示例仓库迁入后，仓库根应识别为 desktop-app 自身而非上级目录。"""
    store = ContractStore.for_base_dir(base_dir=APP_DIR)
    assert store.data_root == APP_DIR  # v2：集合树根（原名 _source_root）


def test_load_examples(items):
    # 2026-09-23 调整基线：Turtle 变体精简（345），新增实用工具箱 50 条
    assert len(items) > 1400
    some = next(iter(items.values()))
    assert some.category in {"topics", "tools", "projects", "json"}
    # v1 兼容窗口内源码还是内联 code（尚未外移）；两种形态都必须能取到源码
    assert some.path.suffix == ".py" and some.json_id
    # 源码可得：v1 兼容期来自清单内联 code，迁移后来自真实文件（两种形态都要能取到）
    store = ContractStore.for_base_dir(base_dir=APP_DIR)
    store.load()
    assert store.get_code(store.index[some.json_id]) != ""


def test_materialize_keeps_sibling_files(items):
    """目录型示例的兄弟数据文件随工作区到位（v2：load 不落盘，按需 ensure_workspace）。"""
    ex = items.get("topics_algorithms_cycle-detection_code_example06.py")
    assert ex is not None
    store = ContractStore.for_base_dir(base_dir=APP_DIR)
    store.load()
    item = store.index["topics_algorithms_cycle-detection_code_example06.py"]
    workspace = store.ensure_workspace(item)
    assert workspace is not None
    assert (workspace / "dictionary.txt").is_file()


def test_save_item_writes_back_real_file(tmp_path):
    """v2 保存：只落真实文件（不再回写内联 code），清单不被改动。"""
    coll = tmp_path / "json_examples"
    coll.mkdir()
    json_file = coll / "demo.json"
    json_file.write_text(
        json.dumps(
            {
                "name": "demo",
                "examples": [
                    {"id": "demo_a", "name": "a.py", "code": "print('a')\n"},
                    {"id": "demo_b", "name": "b.py", "code": "print('b')\n"},
                ],
            }
        ),
        encoding="utf-8",
    )
    # 先把夹具迁移成 v2 形态（真实文件 + file 字段），再验证保存写真实文件
    (coll / "demo").mkdir()
    (coll / "demo" / "a.py").write_text("print('a')\n", encoding="utf-8")
    (coll / "demo" / "b.py").write_text("print('b')\n", encoding="utf-8")
    json_file.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "name": "demo",
                "examples": [
                    {"id": "demo_a", "name": "a.py", "file": "demo/a.py"},
                    {"id": "demo_b", "name": "b.py", "file": "demo/b.py"},
                ],
            }
        ),
        encoding="utf-8",
    )
    before = json_file.read_bytes()
    store = ContractStore.for_base_dir(base_dir=tmp_path)
    item = _flat(store.load())["demo_a"]

    assert store.save_item(item, "print('a2')\n") is True
    assert (coll / "demo" / "a.py").read_text(encoding="utf-8") == "print('a2')\n"
    assert json_file.read_bytes() == before  # 清单是元数据，不再随编辑变动


def test_save_item_survives_midwrite_failure(tmp_path, monkeypatch):
    """写盘中途失败（文件已被截断）不得损坏 JSON 真相源。

    save_item 必须走"临时文件 + 原子替换"：写入失败时原集合文件保持完好、
    无 .tmp 残留。直接原地覆盖写会让整个集合（几十上百个示例）丢失。
    """
    coll = tmp_path / "json_examples"
    coll.mkdir()
    spec = {"id": "demo", "name": "demo.py", "title": "Demo", "code": "print('v1')\n"}
    json_file = coll / "demo.json"
    json_file.write_text(json.dumps({"name": "demo", "examples": [spec]}), encoding="utf-8")

    store = ContractStore.for_base_dir(base_dir=tmp_path)
    root = store.load()
    item = root.children[0].children[0]

    real_write_text = Path.write_text
    state = {"failed": False}

    def flaky_write_text(self, data, **kwargs):
        # 只让集合目录内的首次写入失败（模拟截断已发生后的磁盘故障）：
        # 先按真实行为打开 'w' 模式（截断文件），再抛错——
        # 旧实现在此截断 json_file 本体，新实现截断的应是 .tmp 临时文件
        if not state["failed"] and str(self).startswith(str(coll)):
            state["failed"] = True
            with open(self, "w", encoding="utf-8"):
                pass
            raise OSError("simulated mid-write failure")
        return real_write_text(self, data, **kwargs)

    monkeypatch.setattr(Path, "write_text", flaky_write_text)
    try:
        assert store.save_item(item, "print('v2')\n") is False
    finally:
        monkeypatch.undo()

    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data["examples"][0]["code"] == "print('v1')\n"
    assert list(coll.glob("*.tmp")) == []


def test_materialize_rejects_path_traversal(tmp_path):
    """JSON 的 dir/name 字段不得把物化引到缓存目录之外（绝对路径 / .. 穿越）。"""
    # 仓库根标记：让 _find_repo_root 识别 tmp_path 为 source_root
    for d in ("topics", "tools", "projects"):
        (tmp_path / d).mkdir()
    # 绝对路径指向 tmp_path 之外的小目录（RED 阶段旧实现会把它整个拷入缓存）
    outside = tmp_path.parent / f"trav_outside_{os.getpid()}"
    outside.mkdir(exist_ok=True)
    (outside / "secret.txt").write_text("sensitive", encoding="utf-8")
    coll = tmp_path / "json_examples"
    coll.mkdir()
    evil_dir = {"id": "evil_abs", "name": "e1.py", "code": "print('x')", "dir": str(outside)}
    evil_name = {"id": "evil_name", "name": "../outside.py", "code": "print('x')"}
    (coll / "evil.json").write_text(json.dumps({"name": "evil", "examples": [evil_dir, evil_name]}), encoding="utf-8")
    try:
        store = ContractStore.for_base_dir(base_dir=tmp_path)
        root = store.load()
        # v2：name 越界的条目在校验期被拒；dir 字段彻底退役（不再拷贝任何外部目录）
        loaded = [c.json_id for c in (root.children[0].children if root.children else [])]
        assert "evil_name" not in loaded
        for item in store.index.values():
            store.ensure_workspace(item)  # 即便对 dir 越界条目建工作区，也不得产生越界内容
        assert not (tmp_path / ".json_examples_cache" / "secret.txt").exists()
        assert not (tmp_path / "outside.py").exists()
        assert (outside / "secret.txt").read_text(encoding="utf-8") == "sensitive"  # 外部目录原样未动
    finally:
        shutil.rmtree(outside, ignore_errors=True)


def test_materialize_allows_normal_relative_dir(tmp_path):
    """正常相对 dir 与文件名不受路径校验影响。"""
    # 仓库根标记：让 _find_repo_root 识别 tmp_path 为 source_root
    for d in ("tools", "projects"):
        (tmp_path / d).mkdir()
    src = tmp_path / "topics" / "demo"
    src.mkdir(parents=True)
    (src / "data.txt").write_text("hello", encoding="utf-8")
    coll = tmp_path / "json_examples"
    coll.mkdir()
    (coll / "ok.json").write_text(
        json.dumps(
            {
                "name": "ok",
                "examples": [
                    {"id": "ok_1", "name": "ok1.py", "code": "print('ok')", "dir": "topics/demo"},
                    {"id": "ok_2", "name": "ok2.py", "code": "print('ok2')"},
                ],
            }
        ),
        encoding="utf-8",
    )
    store = ContractStore.for_base_dir(base_dir=tmp_path)
    root = store.load()
    children = root.children[0].children
    assert len(children) == 2
    # 兄弟数据文件随工作区到位（v2：load 不落盘）
    workspace = store.ensure_workspace(children[0])
    assert workspace is not None
    assert (workspace / "data.txt").is_file()


def test_security_checker_detects_risky_code(tmp_path):
    risky = tmp_path / "risky.py"
    risky.write_text("import shutil\nshutil.rmtree('/tmp/x')\n", encoding="utf-8")
    report = SecurityChecker().check(risky)
    assert report.risks, "rmtree 应被判定为风险"


def test_security_checker_passes_clean_code(tmp_path):
    clean = tmp_path / "clean.py"
    clean.write_text("print('hello')\n", encoding="utf-8")
    report = SecurityChecker().check(clean)
    assert not report.risks


def test_security_risk_level_rmtree_is_high(tmp_path):
    """shutil.rmtree 递归删除应判定为高风险。"""
    from app.security import RiskLevel

    risky = tmp_path / "risky.py"
    risky.write_text("import shutil\nshutil.rmtree('/tmp/x')\n", encoding="utf-8")
    report = SecurityChecker().check(risky)
    assert report.max_risk_level == RiskLevel.HIGH
    assert any(r.level == RiskLevel.HIGH for r in report.risk_details)


def test_security_risk_level_subprocess_no_shell_is_medium(tmp_path):
    """subprocess.run 无 shell=True 应判定为中风险（常见操作）。"""
    from app.security import RiskLevel

    code = tmp_path / "sub.py"
    code.write_text("import subprocess\nsubprocess.run(['ls', '-la'])\n", encoding="utf-8")
    report = SecurityChecker().check(code)
    assert report.max_risk_level == RiskLevel.MEDIUM
    assert not report.high_risks


def test_security_risk_level_subprocess_shell_true_is_high(tmp_path):
    """subprocess.run(shell=True) 应判定为高风险（命令注入）。"""
    from app.security import RiskLevel

    code = tmp_path / "shell.py"
    code.write_text("import subprocess\nsubprocess.run('ls', shell=True)\n", encoding="utf-8")
    report = SecurityChecker().check(code)
    assert report.max_risk_level == RiskLevel.HIGH
    assert any("shell=True" in r for r in report.high_risks)


def test_security_risk_level_eval_is_high(tmp_path):
    """eval() 任意代码执行应判定为高风险。"""
    from app.security import RiskLevel

    code = tmp_path / "eval.py"
    code.write_text("eval('1+1')\n", encoding="utf-8")
    report = SecurityChecker().check(code)
    assert report.max_risk_level == RiskLevel.HIGH


def test_security_whitelist_by_id(tmp_path):
    """白名单中的示例 ID 应跳过安全扫描。"""
    code = tmp_path / "safe.py"
    code.write_text("import shutil\nshutil.rmtree('/tmp/x')\n", encoding="utf-8")
    checker = SecurityChecker(whitelist_ids={"my_safe_example"})
    report = checker.check(code, example_id="my_safe_example")
    assert report.is_safe
    assert not report.risks


def test_security_whitelist_by_pattern(tmp_path):
    """白名单 glob 模式匹配的示例 ID 应跳过安全扫描。"""
    code = tmp_path / "safe.py"
    code.write_text("import shutil\nshutil.rmtree('/tmp/x')\n", encoding="utf-8")
    checker = SecurityChecker(whitelist_patterns=["pil_*", "dataviz_*"])
    report = checker.check(code, example_id="pil_image_filter_01")
    assert report.is_safe
    assert not report.risks


def test_security_non_whitelisted_still_scanned(tmp_path):
    """不在白名单中的示例应正常扫描。"""
    code = tmp_path / "risky.py"
    code.write_text("import shutil\nshutil.rmtree('/tmp/x')\n", encoding="utf-8")
    checker = SecurityChecker(whitelist_ids={"other_example"})
    report = checker.check(code, example_id="my_risky_example")
    assert not report.is_safe
    assert report.risks


def test_quality_scoring(items):
    ex = items.get("hello_world") or next(iter(items.values()))
    report = QualityScorer().score(ex)
    assert 0 <= report.score <= 100


def test_venv_manager_python_exe_override(tmp_path):
    override = VenvManager(repo_root=tmp_path, python_exe="/opt/fake/python3")
    assert override.python_exe == "/opt/fake/python3"

    default = VenvManager(repo_root=tmp_path)
    assert default.python_exe == sys.executable


def test_bootstrap_prefers_project_manifest(tmp_path, monkeypatch):
    """引导安装优先使用仓库根的共享依赖清单（requirements.txt）。"""
    installed: list[str] = []
    mgr = VenvManager(repo_root=tmp_path, bootstrap_packages=("fallback-pkg",))

    def fake_pip_install(args, timeout):
        installed.append(args[0])
        return True

    def fake_create_venv():
        mgr.get_python_executable().parent.mkdir(parents=True, exist_ok=True)
        return True

    monkeypatch.setattr(mgr, "_pip_install", fake_pip_install)
    monkeypatch.setattr(mgr, "_create_venv", fake_create_venv)

    # 清单缺失 → 回退内置兜底清单
    mgr.prepare()
    assert "fallback-pkg" in installed

    # 有清单 → 按清单安装（忽略注释），不再用兜底
    installed.clear()
    (tmp_path / "requirements.txt").write_text("# 项目清单\nrequests\ndjango\n\n", encoding="utf-8")
    marker = mgr.venv_path / mgr.MARKER_FILE_NAME
    marker.unlink(missing_ok=True)
    mgr._marker_loaded = False
    mgr.prepare()
    assert "requests" in installed and "django" in installed
    assert "fallback-pkg" not in installed


def test_ensure_python_uses_shared_venv(tmp_path, monkeypatch):
    """所有示例统一使用共享 .venv：requirements 按内容 hash 去重后装入同一环境。"""
    calls: list[tuple] = []
    mgr = VenvManager(repo_root=tmp_path, bootstrap_packages=())

    def fake_create_venv():
        mgr.get_python_executable().parent.mkdir(parents=True, exist_ok=True)
        return True

    def fake_pip_install(args, timeout):
        calls.append(tuple(args))
        return True

    monkeypatch.setattr(mgr, "_create_venv", fake_create_venv)
    monkeypatch.setattr(mgr, "_pip_install", fake_pip_install)

    example = tmp_path / "examples" / "demo.py"
    example.parent.mkdir(parents=True)
    (example.parent / "requirements.txt").write_text("requests\n", encoding="utf-8")

    ok, python_exe = mgr.ensure_python(example)
    assert ok is True
    assert Path(python_exe) == mgr.get_python_executable()
    assert tmp_path / ".venv" in Path(python_exe).parents
    # 首次：创建 venv 并安装示例 requirements
    assert ("-r", str(example.parent / "requirements.txt")) in calls

    # 第二次：hash 已记录，不再触发 pip
    mgr.ensure_python(example)
    pip_calls = [c for c in calls if c and c[0] == "-r"]
    assert len(pip_calls) == 1


def test_shared_venv_without_requirements_skips_pip(tmp_path, monkeypatch):
    """无 requirements.txt 的示例直接用共享 venv 解释器，不触发安装。"""
    calls: list[tuple] = []

    def fake_create_venv():
        calls.append(("create",))
        return True

    def fake_pip_install(args, timeout):
        calls.append(tuple(args))
        return True

    mgr = VenvManager(repo_root=tmp_path, bootstrap_packages=())
    monkeypatch.setattr(mgr, "_create_venv", fake_create_venv)
    monkeypatch.setattr(mgr, "_pip_install", fake_pip_install)

    example = tmp_path / "solo.py"
    example.write_text("print('hi')\n", encoding="utf-8")
    ok, _ = mgr.ensure_python(example)

    assert ok is True
    assert calls == [("create",)]


def test_workspace_requirements_drops_invalid_names(tmp_path):
    """乱码/非法包名（历史迁移数据）不应写进工作区 requirements.txt 污染共享 venv。"""
    coll = tmp_path / "json_examples"
    coll.mkdir()
    (coll / "deps").mkdir()
    (coll / "deps" / "x.py").write_text("print(1)\n", encoding="utf-8")
    (coll / "deps.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "name": "deps",
                "examples": [
                    {
                        "id": "x",
                        "name": "x.py",
                        "file": "deps/x.py",
                        "requirements": ["\x00F\x00l\x00a\x00s\x00k\x00", "requests", "ok-pkg_2"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    store = ContractStore.for_base_dir(base_dir=tmp_path)
    store.load()
    workspace = store.ensure_workspace(store.index["x"])
    lines = (workspace / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert lines == ["requests", "ok-pkg_2"]


# --------------------------------------------------------------------- 用户集合（解耦）


def _make_two_source_store(tmp_path):
    """内置库（json_examples/）+ 用户库（user_examples/）各一个集合。"""
    coll = tmp_path / "json_examples"
    coll.mkdir()
    (coll / "builtin.json").write_text(
        json.dumps({"name": "builtin", "examples": [{"id": "b1", "name": "b1.py", "code": "print(1)\n"}]}),
        encoding="utf-8",
    )
    user = tmp_path / "user_examples"
    user.mkdir()
    (user / "mine.json").write_text(
        json.dumps(
            {
                "name": "mine",
                "examples": [
                    {"id": "u1", "name": "u1.py", "code": "print(2)\n"},
                    {"id": "u2", "name": "u2.py", "code": "print(3)\n"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return ContractStore.for_base_dir(base_dir=tmp_path, user_dir=user), user


def _flat(root):
    flat: dict[str, ExampleItem] = {}

    def walk(item):
        if not item.is_dir and item.json_id:
            flat[item.json_id] = item
        for child in item.children:
            walk(child)

    walk(root)
    return flat


def test_user_dir_loads_alongside_builtin(tmp_path):
    store, _ = _make_two_source_store(tmp_path)
    flat = _flat(store.load())
    assert {"b1", "u1", "u2"} <= set(flat)


def test_source_dir_survives_load(tmp_path):
    """JSON 条目的 dir 字段透传到 item.source_dir（工具箱分组依据）；无 dir 条目为 None。"""
    coll = tmp_path / "json_examples"
    coll.mkdir()
    (coll / "tools.json").write_text(
        json.dumps(
            {
                "name": "tools",
                "examples": [
                    {"id": "t1", "name": "t1.py", "code": "print(1)\n", "dir": "tools/utility-crawlers"},
                    {"id": "t2", "name": "t2.py", "code": "print(2)\n"},
                ],
            }
        ),
        encoding="utf-8",
    )
    store = ContractStore.for_base_dir(base_dir=tmp_path, user_dir=tmp_path / "user_examples")
    flat = _flat(store.load())
    assert flat["t1"].source_dir == "tools/utility-crawlers"
    assert flat["t2"].source_dir is None


def test_user_collection_flag_distinguishes_source(tmp_path):
    store, _ = _make_two_source_store(tmp_path)
    flat = _flat(store.load())
    assert store.is_user_collection(flat["u1"].json_file) is True
    assert store.is_user_collection(flat["b1"].json_file) is False
    assert store.is_user_collection(None) is False


def test_delete_user_example_cleans_manifest_file_and_workspace(tmp_path):
    """删除 = 清单条目 + 真实文件 + 工作区三处同步清理（契约 §5）。"""
    store, user = _make_two_source_store(tmp_path)
    flat = _flat(store.load())
    assert store.ensure_run_status(flat["u1"])  # 预热派生缓存
    workspace = store.ensure_workspace(flat["u1"])
    assert workspace is not None and workspace.is_dir()  # 工作区已建

    assert store.delete_user_example(flat["u1"]) is True
    data = json.loads((user / "mine.json").read_text(encoding="utf-8"))
    assert [s["id"] for s in data["examples"]] == ["u2"]
    assert not workspace.exists()  # 工作区一并清理
    assert "u1" not in store._run_status and "u1" not in store.index


def test_delete_refuses_builtin_and_missing(tmp_path):
    store, _ = _make_two_source_store(tmp_path)
    flat = _flat(store.load())
    # 内置集合受保护
    assert store.delete_user_example(flat["b1"]) is False
    assert "b1" in (tmp_path / "json_examples" / "builtin.json").read_text(encoding="utf-8")
    # 集合里已无此条目时返回 False
    ghost = ExampleItem(
        name="ghost.py",
        path=tmp_path / "x.py",
        is_dir=False,
        category="json",
        source="json",
        code="",
        json_id="ghost",
        json_file=tmp_path / "user_examples" / "mine.json",
    )
    assert store.delete_user_example(ghost) is False


def test_delete_last_example_removes_collection_file(tmp_path):
    """集合删空后整个集合文件移除，加载侧不再生成空 📦 节点。"""
    store, user = _make_two_source_store(tmp_path)
    flat = _flat(store.load())
    assert store.delete_user_example(flat["u1"]) is True
    assert store.delete_user_example(flat["u2"]) is True
    assert not (user / "mine.json").exists()
    # 重新加载：用户集合节点消失
    root = store.load()
    coll_names = [c.name for c in root.children]
    assert not any("mine" in n for n in coll_names)


def test_version_single_source_is_in_sync():
    """版本号单一来源（仓库根 VERSION）与各处生成物一致——CI 门禁的本地等价。"""
    from app._version import __version__ as app_version

    version = (APP_DIR / "VERSION").read_text(encoding="utf-8").strip()
    assert app_version == version
    pkg = json.loads((APP_DIR / "electron-prototype" / "electron" / "package.json").read_text(encoding="utf-8"))
    assert pkg["version"] == version
    assert f'version = "{version}"' in (APP_DIR / "pyproject.toml").read_text(encoding="utf-8")


def test_bootstrap_prefers_lock_file_over_manifest(tmp_path, monkeypatch):
    """锁文件（requirements.lock.txt，全钉版本）优先于未钉版 requirements.txt——
    首启装包可复现，不随 PyPI 上新漂移（审计 P1：运行时依赖零锁定）。"""
    installed: list[str] = []
    mgr = VenvManager(repo_root=tmp_path, bootstrap_packages=("fallback-pkg",))

    def fake_pip_install(args, timeout):
        installed.extend(args)
        return True

    def fake_create_venv():
        mgr.get_python_executable().parent.mkdir(parents=True, exist_ok=True)
        return True

    monkeypatch.setattr(mgr, "_pip_install", fake_pip_install)
    monkeypatch.setattr(mgr, "_create_venv", fake_create_venv)

    (tmp_path / "requirements.txt").write_text("requests\n", encoding="utf-8")
    (tmp_path / "requirements.lock.txt").write_text(
        "# 由 uv pip compile 生成（勿手改）：uv pip compile requirements.txt -o requirements.lock.txt --universal\n"
        "requests==2.32.3\n",
        encoding="utf-8",
    )
    mgr.prepare()

    assert "requests==2.32.3" in installed
    assert "requests" not in installed  # 未钉版条目不得混入
    assert "fallback-pkg" not in installed


def test_example_requirements_falls_back_to_per_line_and_caches_attempt(tmp_path, monkeypatch):
    """-r 整体安装失败（课程 requirements.txt 常含 PyPI 上不存在的名字，如 ternary-new）
    必须降级为逐行安装：坏名字跳过、好名字装上；且尝试过后记录 hash——
    否则每次运行都重试注定失败的解析，示例在 run_id 之后长时间无输出（2026-10-02 用户实测）。"""
    installed: list[str] = []
    calls: list[list[str]] = []
    mgr = VenvManager(repo_root=tmp_path, bootstrap_packages=())

    def fake_pip_install(args, timeout):
        calls.append(list(args))
        if args and args[0] == "-r":
            return False  # 整体解析失败（uv: No solution found）
        if args and args[0] == "ternary-new":
            return False  # PyPI 上不存在，逐行安装时也失败
        installed.extend(a for a in args if not a.startswith("-"))
        return True

    def fake_create_venv():
        mgr.get_python_executable().parent.mkdir(parents=True, exist_ok=True)
        return True

    monkeypatch.setattr(mgr, "_pip_install", fake_pip_install)
    monkeypatch.setattr(mgr, "_create_venv", fake_create_venv)

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "requirements.txt").write_text(
        "requests\nternary-new\n# comment\n\nflask\n-e .\n", encoding="utf-8"
    )
    mgr._install_example_requirements(ws / "app.py")

    # 整体安装尝试了一次，随后逐行兜底：requests/flask 装上，ternary-new/-e 跳过
    assert calls[0][0] == "-r"
    assert "requests" in installed and "flask" in installed
    assert "ternary-new" not in installed
    # 尝试过就记 hash：下次运行不再重试
    import hashlib

    digest = hashlib.sha256((ws / "requirements.txt").read_bytes()).hexdigest()
    assert mgr._load_marker().get("requirements", {}).get(digest) is True
