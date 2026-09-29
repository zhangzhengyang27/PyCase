"""regression_smoke 纯函数单元测试：分类、必填参数识别、分层抽样与基线对比。"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "electron-prototype" / "sidecar"))

from app.models import ExampleItem  # noqa: E402

import regression_smoke as rs  # noqa: E402


def _make_item(
    name: str, category: str = "topics", code: str = "print('x')\n", idx: int = 0
) -> ExampleItem:
    return ExampleItem(
        name=name,
        path=ROOT / category / name,
        is_dir=False,
        category=category,
        code=code,
        json_id=f"{category}/{name}-{idx}",
    )


# ---------------------------------------------------------------------------
# classify_output
# ---------------------------------------------------------------------------
class TestClassifyOutput:
    def test_pass(self):
        assert rs.classify_output(0, "ok\n") == ("pass", "")

    def test_missing_dependency(self):
        status, _ = rs.classify_output(
            1, "Traceback\nModuleNotFoundError: No module named 'foo'"
        )
        assert status == "missing_dependency"

    def test_import_error_also_missing(self):
        status, _ = rs.classify_output(1, "ImportError: cannot import name X")
        assert status == "missing_dependency"

    def test_syntax_error(self):
        status, _ = rs.classify_output(1, "  SyntaxError: invalid syntax")
        assert status == "syntax_error"

    def test_plain_failure_keeps_tail(self):
        status, reason = rs.classify_output(2, "line1\nValueError: bad")
        assert status == "failed"
        assert "ValueError" in reason


# ---------------------------------------------------------------------------
# needs_arguments
# ---------------------------------------------------------------------------
class TestNeedsArguments:
    def test_no_args(self):
        assert rs.needs_arguments("print('hello')\n") is False

    def test_required_option(self):
        code = "import argparse\np=argparse.ArgumentParser()\np.add_argument('--name', required=True)\np.parse_args()\n"
        assert rs.needs_arguments(code) is True

    def test_positional_without_default(self):
        code = "import argparse\np=argparse.ArgumentParser()\np.add_argument('path')\np.parse_args()\n"
        assert rs.needs_arguments(code) is True

    def test_optional_with_default_not_needed(self):
        code = "import argparse\np=argparse.ArgumentParser()\np.add_argument('--n', type=int, default=1)\np.parse_args()\n"
        assert rs.needs_arguments(code) is False


# ---------------------------------------------------------------------------
# stratified_sample
# ---------------------------------------------------------------------------
class TestStratifiedSample:
    def test_deterministic_with_seed(self):
        leaves = [_make_item(f"a{i}.py", "topics", idx=i) for i in range(40)]
        first = rs.stratified_sample(leaves, 0.1, 42)
        second = rs.stratified_sample(leaves, 0.1, 42)
        assert [x.json_id for x in first] == [x.json_id for x in second]

    def test_every_nonempty_stratum_represented(self):
        leaves = (
            [_make_item(f"t{i}.py", "topics", idx=i) for i in range(30)]
            + [_make_item(f"x{i}.py", "tools", idx=i) for i in range(3)]
            + [_make_item(f"p{i}.py", "projects", idx=i) for i in range(2)]
        )
        picked = rs.stratified_sample(leaves, 0.1, 7)
        categories = {x.category for x in picked}
        assert {"topics", "tools", "projects"} <= categories

    def test_all_ratio_returns_everything(self):
        leaves = [_make_item(f"a{i}.py", idx=i) for i in range(10)]
        picked = rs.stratified_sample(leaves, 1.0, 1)
        assert len(picked) == 10

    def test_family_booster_guarantees_coverage(self):
        # 99 个普通示例 + 1 个 pygame 示例；比例抽样很容易漏掉唯一的家族样本，补足逻辑必须捞回
        leaves = [_make_item(f"a{i}.py", idx=i) for i in range(99)]
        leaves.append(
            _make_item("game.py", code="import pygame\npygame.init()\n", idx=99)
        )
        picked = rs.stratified_sample(leaves, 0.05, 1)
        assert any("pygame" in (x.code or "") for x in picked)

    def test_limit_caps_size(self):
        leaves = [_make_item(f"a{i}.py", idx=i) for i in range(60)]
        assert len(rs.stratified_sample(leaves, 1.0, 1, limit=5)) == 5


# ---------------------------------------------------------------------------
# compare_baseline
# ---------------------------------------------------------------------------
class TestCompareBaseline:
    def _baseline(self, tmp: Path, entries: list[dict]) -> Path:
        p = tmp / "baseline.json"
        p.write_text(json.dumps({"results": entries}), encoding="utf-8")
        return p

    def test_pass_to_failed_is_regression(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = self._baseline(Path(d), [{"id": "t/a.py-0", "status": "pass"}])
            result = rs.RunResult("t/a.py-0", "a.py", "topics", "failed", 0.1, "boom")
            regressions = rs.compare_baseline([result], baseline)
            assert len(regressions) == 1

    def test_pass_to_timeout_not_counted(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = self._baseline(Path(d), [{"id": "t/a.py-0", "status": "pass"}])
            result = rs.RunResult("t/a.py-0", "a.py", "topics", "timeout", 8.0, "")
            assert rs.compare_baseline([result], baseline) == []

    def test_already_failing_not_regression(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = self._baseline(Path(d), [{"id": "t/a.py-0", "status": "failed"}])
            result = rs.RunResult("t/a.py-0", "a.py", "topics", "failed", 0.1, "")
            assert rs.compare_baseline([result], baseline) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
