"""清单再生成守卫测试（2026-10 体检 P2 收口）。

背景：语料大退役（1464→395）后，历史生成器（gen_sciviz_examples /
gen_real_projects）重跑会把已退役条目写回清单。守卫把「当前清单」当真相，
生成 id 集与目标清单 id 集双向不对账即中止。本文件钉守卫逻辑本身；
两台生成器的接线由「真清单驱动 Collection.save / gen_sciviz main」实测验证。
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generator_guard import guard_regen  # noqa: E402


def _manifest(tmp_path: Path, ids: list[str]) -> Path:
    p = tmp_path / "m.json"
    p.write_text(
        json.dumps({"examples": [{"id": i} for i in ids]}, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


def _generated(ids: list[str]) -> list[dict]:
    return [{"id": i} for i in ids]


def test_id_set_equal_passes(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    target = _manifest(tmp_path, ["a", "b"])
    guard_regen(target, _generated(["b", "a"]), tool="t")
    assert capsys.readouterr().out == ""


def test_resurrected_id_aborts(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    target = _manifest(tmp_path, ["a"])
    with pytest.raises(SystemExit) as e:
        guard_regen(target, _generated(["a", "retired-x"]), tool="t")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "retired-x" in err and "复活" in err


def test_dropped_id_aborts(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    target = _manifest(tmp_path, ["a", "b"])
    with pytest.raises(SystemExit) as e:
        guard_regen(target, _generated(["a"]), tool="t")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "丢失" in err and "b" in err


def test_missing_target_treated_as_empty_requires_force(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    target = tmp_path / "absent.json"
    with pytest.raises(SystemExit):
        guard_regen(target, _generated(["a"]), tool="t")
    guard_regen(target, _generated(["a"]), tool="t", force=True)
    assert "force" in capsys.readouterr().out


def test_force_bypasses_with_warning(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    target = _manifest(tmp_path, ["a"])
    guard_regen(target, _generated(["a", "retired-x"]), tool="t", force=True)
    assert "豁免" in capsys.readouterr().out
