"""G8 迁移护栏：在**真实数据的完整副本**上跑通 dry-run → apply → verify → rollback。

契约 §6.2 的演练纪律：切换真相源之前，必须先在副本上把四步走通，1496/1496 逐条等价。
本用例就是那条纪律的可执行形式——它不碰仓库里的真相源（全程在 tmp 副本上）。

另外钉住 dry-run 的规模事实（1426 create / 70 原位），来自 B1 审计对现状数据的分类：
单文件 1395 + 目录型补缺 31 = 1426；目录型原位 = 70。数字对不上说明数据或迁移逻辑变了，
必须人工确认后再动真相源。
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.migration import apply_plan, build_plan, rollback, verify_migration  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# 演练只需清单与源码树；examples_assets（102MB 素材）与迁移无关，跳过以保持用例轻量
TREES = ("json_examples", "topics", "tools", "projects")


def _copy_tree(tmp: Path) -> Path:
    tree = tmp / "tree"
    tree.mkdir()
    for name in TREES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, tree / name)
    return tree


def _pristine(tree: Path) -> None:
    """核对副本已回到 v1：清单无 schema_version、外移目录不存在、原位目录未被改动。"""
    for manifest in sorted((tree / "json_examples").glob("*.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert "schema_version" not in data, f"{manifest.name} 仍是 v2"
        assert all(
            "file" not in e for e in data["examples"]
        ), f"{manifest.name} 仍带 file 字段"
    assert list((tree / "json_examples").glob("*.py")) == []
    assert not (tree / "json_examples" / "bulk_basics").exists()


def test_g8_migration_drill_on_real_data_copy(tmp_path):
    tree = _copy_tree(tmp_path)
    builtin = tree / "json_examples"
    user_root = tree / "user_examples"

    # 1) dry-run：规模与审计分类一致，且零错误零警告
    plan = build_plan(builtin, tree, user_root)
    assert plan.errors == [], [i.message for i in plan.errors]
    s = plan.summary()
    assert s["collections"] == 14
    assert s["entries"] == 1496
    assert s["writes"] == {"create": 1426, "verify-in-place": 70}
    # dry-run 不落盘
    assert list(builtin.glob("*.py")) == []

    # 2) apply + 复验：逐条等价
    snapshot = {
        m.path: json.loads(m.path.read_text(encoding="utf-8")) for m in plan.manifests
    }
    ts, backup_dirs = apply_plan(plan, lambda manifest: manifest.parent / ".backup")
    assert ts and backup_dirs
    issues = verify_migration(
        [m.path for m in plan.manifests], snapshot, plan.renamed_ids
    )
    assert issues == [], [f"{i.code}: {i.message}" for i in issues[:5]]

    # 迁移后的形态：清单为 v2、外移文件真实存在、内容与 v1 code 逐字节相等
    manifest = builtin / "bulk_basics.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    first = data["examples"][0]
    assert "code" not in first and first["file"].startswith("bulk_basics/")
    assert (builtin / first["file"]).read_text(encoding="utf-8") == snapshot[manifest][
        "examples"
    ][0]["code"]

    # 3) rollback：回到 v1，且不漏空目录
    rollback(backup_dirs)
    _pristine(tree)


def test_g8_plan_is_idempotent_after_apply(tmp_path):
    """迁移后再跑 dry-run：不应再产生计划（否则会重复外移）。"""
    tree = _copy_tree(tmp_path)
    builtin = tree / "json_examples"
    plan = build_plan(builtin, tree, tree / "user_examples")
    apply_plan(plan, lambda manifest: manifest.parent / ".backup")
    again = build_plan(builtin, tree, tree / "user_examples")
    assert again.manifests == [] and again.errors == []
