"""契约 v1 → v2 迁移工具测试（B2-2）。

在**合成的小型集合树**上覆盖四类变更与四步流程：单文件外移、目录型原位/补缺、
顶层 name 补齐、id 冲突改名；apply 先备份、verify 逐字节、rollback 还原并删新建文件。
真实 1496 条的演练是 G8 护栏（另一个文件），这里用合成数据把规则钉死。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.migration import apply_plan, build_plan, rollback, verify_migration  # noqa: E402


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _tree(tmp: Path) -> Path:
    """造一棵小型集合树：两个内置集合（单文件 + 目录型）+ 一个用户集合。"""
    root = tmp / "tree"
    builtin = root / "json_examples"
    user_root = root / "user_examples"
    # 集成一：两个单文件示例
    _write(
        builtin / "alpha.json",
        {
            "name": "甲集合",
            "examples": [
                {
                    "id": "a1",
                    "name": "one.py",
                    "title": "一",
                    "category": "topics",
                    "tags": ["基础"],
                    "code": "print(1)\n",
                },
                {
                    "id": "a2",
                    "name": "two.py",
                    "title": "二",
                    "category": "topics",
                    "code": "print(2)\n",
                    "custom": "keep-me",
                },
            ],
        },
    )
    # 集合二：目录型（原位文件一致）+ 目录型（目标缺失）
    (root / "tools" / "proj").mkdir(parents=True)
    (root / "tools" / "proj" / "inplace.py").write_text(
        "print('inplace')\n", encoding="utf-8"
    )
    _write(
        builtin / "beta.json",
        {
            "examples": [
                {
                    "id": "b1",
                    "name": "inplace.py",
                    "category": "tools",
                    "dir": "tools/proj",
                    "code": "print('inplace')\n",
                },
                {
                    "id": "b2",
                    "name": "missing.py",
                    "category": "tools",
                    "dir": "tools/proj",
                    "code": "print('missing')\n",
                },
                {
                    "id": "b3",
                    "name": "plain.py",
                    "category": "tools",
                    "code": "print('plain')\n",
                },
            ]
        },
    )
    # 用户集合：id 与内置冲突
    _write(
        user_root / "mine.json",
        {
            "name": "我的集合",
            "examples": [
                {
                    "id": "a1",
                    "name": "mine.py",
                    "category": "user",
                    "code": "print('mine')\n",
                }
            ],
        },
    )
    return root


def test_plan_shapes_each_class(tmp_path):
    root = _tree(tmp_path)
    plan = build_plan(root / "json_examples", root, root / "user_examples")
    assert not plan.errors, [i.message for i in plan.errors]
    summary = plan.summary()
    # 单文件外移：a1/a2/b3/用户 a1；目录型原位 1 条；目录型补缺 1 条
    assert summary["writes"]["create"] == 5
    assert summary["writes"]["verify-in-place"] == 1
    assert summary["renamed_ids"] == 1
    assert summary["collections"] == 3


def test_apply_then_verify_then_rollback(tmp_path):
    root = tmp_path / "tree"
    _tree(tmp_path)
    builtin = root / "json_examples"
    user_root = root / "user_examples"
    plan = build_plan(builtin, root, user_root)
    snapshot = {
        m.path: json.loads(m.path.read_text(encoding="utf-8")) for m in plan.manifests
    }

    _ts, backup_dirs = apply_plan(plan, lambda manifest: manifest.parent / ".backup")
    issues = verify_migration(
        [m.path for m in plan.manifests], snapshot, plan.renamed_ids
    )
    assert issues == [], [i.message for i in issues]

    # 迁移后：清单为 v2、file 指向真实文件、内容逐字节相等、未知字段保留
    alpha = json.loads((builtin / "alpha.json").read_text(encoding="utf-8"))
    assert alpha["schema_version"] == 2
    assert alpha["examples"][0]["file"] == "alpha/one.py"
    assert "code" not in alpha["examples"][0]
    assert (builtin / "alpha" / "one.py").read_bytes() == b"print(1)\n"
    assert alpha["examples"][1]["custom"] == "keep-me"
    # 目录型：原位文件不动、清单指向 ../tools/…；缺失的那条被补出来
    beta = json.loads((builtin / "beta.json").read_text(encoding="utf-8"))
    files = {e["id"]: e["file"] for e in beta["examples"]}
    assert files["b1"] == "../tools/proj/inplace.py"
    assert files["b2"] == "../tools/proj/missing.py"
    assert (
        root / "tools" / "proj" / "missing.py"
    ).read_bytes() == b"print('missing')\n"
    # 顶层 name 补齐（原缺失，回退 stem）
    assert beta["name"] == "beta"

    # 回滚：清单回到 v1、迁移新建的文件被删除、原位文件保持
    rollback(backup_dirs)
    alpha_back = json.loads((builtin / "alpha.json").read_text(encoding="utf-8"))
    assert "schema_version" not in alpha_back
    assert alpha_back["examples"][0]["code"] == "print(1)\n"
    assert not (builtin / "alpha" / "one.py").exists()
    assert not (root / "tools" / "proj" / "missing.py").exists()
    assert (
        root / "tools" / "proj" / "inplace.py"
    ).read_bytes() == b"print('inplace')\n"


def test_apply_refuses_when_plan_has_errors(tmp_path):
    root = tmp_path / "tree"
    _tree(tmp_path)
    builtin = root / "json_examples"
    # 制造一个 error：目录型条目缺 code
    _write(
        builtin / "gamma.json",
        {"examples": [{"id": "g1", "name": "x.py", "dir": "tools/proj"}]},
    )
    plan = build_plan(builtin, root, root / "user_examples")
    assert plan.errors
    try:
        apply_plan(plan, lambda m: m.parent / ".backup")
    except RuntimeError as e:
        assert "拒绝执行" in str(e)
    else:  # pragma: no cover
        raise AssertionError("报告非空时 apply 必须拒绝")


def test_inplace_content_conflict_is_an_error(tmp_path):
    root = tmp_path / "tree"
    _tree(tmp_path)
    builtin = root / "json_examples"
    # 原位文件与清单 code 不一致：必须暴露，不能静默覆盖
    (root / "tools" / "proj" / "inplace.py").write_text(
        "print('DRIFT')\n", encoding="utf-8"
    )
    plan = build_plan(builtin, root, root / "user_examples")
    assert [i.code for i in plan.errors] == ["dir-content-conflict"]


def test_atomic_write_leaves_no_tmp(tmp_path):
    root = tmp_path / "tree"
    _tree(tmp_path)
    builtin = root / "json_examples"
    plan = build_plan(builtin, root, root / "user_examples")
    apply_plan(plan, lambda m: m.parent / ".backup")
    assert list(builtin.rglob("*.tmp")) == []
    assert list((root / "tools").rglob("*.tmp")) == []


def test_second_run_is_noop(tmp_path):
    """幂等：迁移过的集合不再进计划（避免重复外移）。"""
    root = tmp_path / "tree"
    _tree(tmp_path)
    builtin = root / "json_examples"
    plan = build_plan(builtin, root, root / "user_examples")
    apply_plan(plan, lambda m: m.parent / ".backup")
    again = build_plan(builtin, root, root / "user_examples")
    assert again.manifests == []
    assert again.errors == []
