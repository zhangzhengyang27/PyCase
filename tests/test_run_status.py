"""可运行性判定（app/run_status.py + ExampleStore 接入）的单元测试。

覆盖：五态判定与优先级、模块索引集合运算、本地模块排除、
ExampleStore 的 ensure_run_status / ensure_risk_findings 缓存与回写失效。
不执行任何示例代码。
"""

import json
import sys
from pathlib import Path

from app.json_examples import ExampleStore
from app.run_status import (
    BROKEN,
    EMPTY,
    MISSING_DEPS,
    RISKY,
    RUNNABLE,
    ModuleIndex,
    compute_run_status,
    parse_code,
    third_party_imports,
)
from app.security import SecurityChecker

CHECKER = SecurityChecker()

# 有效代码需 ≥30 字符（空壳阈值），统一用这段作为 runnable 基线
GOOD_CODE = 'name = "world"\nfor i in range(3):\n    print(f"hello {name} {i}")\n'


def make_index(available: bool, modules: set[str] = frozenset()) -> ModuleIndex:
    """构造测试用模块索引（不起子进程枚举）。"""
    idx = ModuleIndex()
    idx.available = available
    idx._modules = frozenset(modules)
    return idx


def status_of(code: str, index: ModuleIndex | None = None) -> str:
    return compute_run_status(code, example_id="t", checker=CHECKER, module_index=index)


# --------------------------------------------------------------------- 五态


def test_runnable_for_normal_code():
    assert status_of(GOOD_CODE) == RUNNABLE


def test_broken_for_syntax_error():
    assert status_of("def broken(:\n    pass\n# padding to exceed thirty chars\n") == BROKEN


def test_empty_for_docstring_only_and_short_code():
    assert status_of('"""只有 docstring 的空壳示例。"""\n') == EMPTY
    assert status_of("print('x')\n") == EMPTY  # < 30 字符


def test_missing_deps_for_unknown_module():
    idx = make_index(True, {"numpy"})
    code = GOOD_CODE + "import pandas as pd\nprint(pd.__version__)\n"
    assert status_of(code, idx) == MISSING_DEPS


def test_risky_for_high_risk_call():
    code = 'import os\nif os.environ.get("GO"):\n    os.system("echo hi")\n'
    assert status_of(code) == RISKY


# --------------------------------------------------------------------- 优先级


def test_missing_deps_beats_risky():
    """又缺依赖又高危：先报缺依赖（能不能跑优先于风险提示）。"""
    idx = make_index(True, set())
    code = 'import notinstalled_pkg\nimport os\nos.system("echo hi")\n'
    assert status_of(code, idx) == MISSING_DEPS


def test_empty_beats_everything():
    idx = make_index(True, set())
    assert status_of('"""docstring"""\n', idx) == EMPTY


# --------------------------------------------------------------------- 模块索引


def test_module_index_missing_modules_excludes_stdlib_and_installed():
    idx = make_index(True, {"pandas", "flask"})
    missing = idx.missing_modules({"pandas", "json", "os", "nope_pkg"})
    assert missing == {"nope_pkg"}


def test_module_index_unavailable_returns_empty():
    assert make_index(False).missing_modules({"anything"}) == set()


def test_module_index_real_interpreter():
    """对当前解释器做真实枚举：至少应发现已安装的 pytest。"""
    idx = ModuleIndex(sys.executable)
    assert idx.available
    assert idx.missing_modules({"pytest"}) == set()


def test_third_party_imports_excludes_local_modules(tmp_path):
    (tmp_path / "sibling_helper.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "localpack").mkdir()
    (tmp_path / "localpack" / "__init__.py").write_text("", encoding="utf-8")
    code = "import sibling_helper\nfrom localpack import thing\nimport json\n"
    tree = parse_code(code)
    mods = third_party_imports(code, tree, [tmp_path])
    assert mods == set()


# --------------------------------------------------------------------- ExampleStore 接入


def make_store(tmp_path: Path, code: str) -> tuple[ExampleStore, object]:
    """构造含单示例的临时 store（照 test_core.py 的回写测试模式）。"""
    coll = tmp_path / "json_examples"
    coll.mkdir()
    spec = {"id": "demo", "name": "demo.py", "title": "Demo", "code": code}
    (coll / "demo.json").write_text(
        json.dumps({"name": "demo", "examples": [spec]}), encoding="utf-8"
    )
    store = ExampleStore(base_dir=tmp_path)
    store.load()
    item = store._root.children[0].children[0]
    return store, item


def test_store_run_status_cached_and_invalidated_by_save(tmp_path):
    store, item = make_store(tmp_path, GOOD_CODE)
    assert store.ensure_run_status(item) == RUNNABLE
    # 缓存命中：篡改内存代码不重算也能读到旧值
    item.code = '"""docstring only"""\n'
    assert store.ensure_run_status(item) == RUNNABLE
    # 回写后缓存失效，按新代码重算
    assert store.save_item(item, '"""docstring only"""\n') is True
    assert store.ensure_run_status(item) == EMPTY


def test_store_risk_findings_feed_risk_high_and_run_status(tmp_path):
    code = 'import os\nif os.environ.get("GO"):\n    os.system("echo hi")\n'
    store, item = make_store(tmp_path, code)
    findings = store.ensure_risk_findings(item)
    assert findings and all("description" in f and "category" in f for f in findings)
    assert store.ensure_risk_high(item) is True
    assert store.ensure_run_status(item) == RISKY


def test_store_missing_deps_requires_module_index(tmp_path):
    store, item = make_store(tmp_path, GOOD_CODE + "import pandas as pd\nprint(pd.__version__)\n")
    # 未注入索引：宁可漏报不误报
    assert store.ensure_run_status(item) == RUNNABLE
    # 注入不含 pandas 的索引后重算为缺依赖
    store.set_module_python(None)
    store._module_index = make_index(True, set())
    store._run_status.clear()
    assert store.ensure_run_status(item) == MISSING_DEPS
