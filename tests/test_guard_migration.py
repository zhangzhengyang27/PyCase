"""G8 迁移护栏：v1 → v2 → 回滚，逐条等价（契约 §6.2）。

演练纪律：切换真相源之前，必须先在**完整副本**上跑通 dry-run → apply → verify → rollback。
本用例是那条纪律的可执行形式：夹具是一份覆盖全部迁移类别的 v1 语料
（单文件外移 / 目录型原位 / 目录型补缺 / 跨集合 id 冲突 / 非法 id 字符 / 缺顶层 name），
全程在 tmp 副本上，不碰仓库真相源。

真实数据的迁移已在 2026-09-29 用同一工具跑过（dry-run 1426 create / 70 原位、0 错误、
apply 后 1496/1496 逐条复验通过），当前仓库数据即其产物；此处的"规模事实"由 G1
（14 集合 / 1496 条）与 G7（协议）钉住，本用例钉住**迁移机制本身**不退化。
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.migration import apply_plan, build_plan, rollback, verify_migration  # noqa: E402
from app import migration_cli  # noqa: E402

# --------------------------------------------------------------------- v1 语料


def _write_v1_corpus(tree: Path) -> None:
    """构造覆盖 §6.1 全部类别的 v1 语料（内置集合 + 原位源码树）。"""
    builtin = tree / "json_examples"
    builtin.mkdir(parents=True)
    (tree / "tools" / "utility-crawlers").mkdir(parents=True)
    (tree / "topics" / "basics").mkdir(parents=True)
    # 目录型·文件已在位（应与 code 逐字节一致）
    inplace = tree / "tools" / "utility-crawlers" / "crawler.py"
    inplace.write_text("print('in-place')\n", encoding="utf-8")

    alpha = {
        "name": "alpha",
        "examples": [
            {"id": "single_a", "name": "single_a.py", "category": "topics", "code": "print('a')\n"},
            {
                "id": "dup",
                "name": "dup.py",
                "category": "topics",
                "code": "import turtle\nprint('dup-alpha')\n",
            },
        ],
    }
    beta = {
        # 顶层 name 缺失：迁移补齐（回退 stem），load 期同样回退
        "examples": [
            {
                "id": "dup",
                "name": "dup.py",
                "category": "topics",
                "code": "print('dup-beta')\n",
            },
            {
                "id": "crawler",
                "name": "crawler.py",
                "category": "tools",
                "code": "print('in-place')\n",
                "dir": "tools/utility-crawlers",
            },
            {
                # 目录型·目标文件缺失：把 code 落成真实文件写进源目录
                "id": "missing_dir",
                "name": "missing.py",
                "category": "tools",
                "code": "print('missing-dir')\n",
                "dir": "tools/utility-crawlers",
            },
            {
                # 非法 id 字符：不判错、只记警告（改名=破坏身份）
                "id": "weird id/中文",
                "name": "weird.py",
                "category": "topics",
                "code": "print('weird')\n",
            },
        ],
    }
    (builtin / "alpha.json").write_text(json.dumps(alpha, ensure_ascii=False), encoding="utf-8")
    (builtin / "beta.json").write_text(json.dumps(beta, ensure_ascii=False), encoding="utf-8")


def _copy_tree(tmp: Path) -> Path:
    tree = tmp / "tree"
    tree.mkdir()
    _write_v1_corpus(tree)
    return tree


def _v1_snapshot(plan) -> dict:
    """迁移前的 v1 清单快照（逐条等价的基线）。"""
    return {m.path: json.loads(m.path.read_text(encoding="utf-8")) for m in plan.manifests}


def _pristine(tree: Path) -> None:
    """核对副本已回到 v1：清单无 schema_version、外移目录不存在、原位目录未被改动。"""
    for manifest in sorted((tree / "json_examples").glob("*.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert "schema_version" not in data, f"{manifest.name} 仍是 v2"
        assert all("file" not in e for e in data["examples"]), f"{manifest.name} 仍带 file 字段"
    assert not (tree / "json_examples" / "alpha").exists()
    assert not (tree / "json_examples" / "beta").exists()
    assert not (tree / "tools" / "utility-crawlers" / "missing.py").exists()


# --------------------------------------------------------------------- 演练


def test_g8_migration_drill_on_full_copy(tmp_path):
    tree = _copy_tree(tmp_path)
    builtin = tree / "json_examples"

    # 1) dry-run：规模与类别一致，零错误
    plan = build_plan(builtin, tree, None)
    assert plan.errors == [], [i.message for i in plan.errors]
    s = plan.summary()
    assert s["collections"] == 2
    assert s["entries"] == 6  # 6 条合法条目（非法 id 只警告，不拒收）
    # 外移/补缺 5 个文件（single_a / dup / dup_2 / missing.py / weird.py），原位 1 个
    assert s["writes"] == {"create": 5, "verify-in-place": 1}
    assert s["renamed_ids"] == 1  # 跨集合 dup → dup_2
    assert s["warnings"] >= 2  # id 冲突改名 + 非法 id 字符 + 缺顶层 name
    # dry-run 不落盘
    assert list(builtin.glob("*.py")) == []
    assert not (builtin / "alpha").exists()

    # 2) apply + 复验：逐条等价（条数 / id 集合 / code↔file 逐字节 / 元数据字段）
    snapshot = _v1_snapshot(plan)
    ts, backup_dirs = apply_plan(plan, lambda manifest: manifest.parent / ".backup")
    assert ts and backup_dirs
    issues = verify_migration([m.path for m in plan.manifests], snapshot, plan.renamed_ids)
    assert issues == [], [f"{i.code}: {i.message}" for i in issues[:5]]

    # 迁移后的形态：v2、外移文件真实存在、内容与 v1 code 逐字节相等
    alpha = json.loads((builtin / "alpha.json").read_text(encoding="utf-8"))
    beta = json.loads((builtin / "beta.json").read_text(encoding="utf-8"))
    assert alpha["schema_version"] == 2 and beta["schema_version"] == 2
    assert beta["name"] == "beta", "顶层 name 缺失应回退 stem 补齐"
    assert all("code" not in e and e["file"] for e in alpha["examples"] + beta["examples"])
    for m in plan.manifests:
        for write in m.writes:
            assert write.path.read_text(encoding="utf-8") == write.content
    # 目录型原位引用写成相对清单目录的路径
    crawler = next(e for e in beta["examples"] if e["id"] == "crawler")
    assert crawler["file"] == "../tools/utility-crawlers/crawler.py"
    # 迁移未改原位文件（仍是 v1 内容）
    assert (tree / "tools" / "utility-crawlers" / "crawler.py").read_text(encoding="utf-8") == "print('in-place')\n"

    # 3) rollback：回到 v1，且不漏空目录
    rollback(backup_dirs)
    _pristine(tree)


def test_g8_plan_is_idempotent_after_apply(tmp_path):
    """迁移后再跑 dry-run：不应再产生计划（否则会重复外移）。"""
    tree = _copy_tree(tmp_path)
    builtin = tree / "json_examples"
    plan = build_plan(builtin, tree, None)
    apply_plan(plan, lambda manifest: manifest.parent / ".backup")
    again = build_plan(builtin, tree, None)
    assert again.manifests == [] and again.errors == []


def test_g8_apply_rejects_non_empty_report(tmp_path):
    """报告非空即拒写：校验错误必须先人工确认，不允许带病迁移。"""
    tree = _copy_tree(tmp_path)
    builtin = tree / "json_examples"
    # 目录型条目与清单 code 不一致：契约只允许"逐字节一致"与"缺失"两态
    (tree / "tools" / "utility-crawlers" / "crawler.py").write_text("print('conflict')\n", encoding="utf-8")
    plan = build_plan(builtin, tree, None)
    assert [i.code for i in plan.errors] == ["dir-content-conflict"]

    # CLI 的 apply 路径必须拒写（而不是"计划里有错但照样落盘"）
    rc = migration_cli.main(
        ["--apply", "--builtin-root", str(builtin), "--data-root", str(tree), "--user-root", str(tree / "user_examples")]
    )
    assert rc == 1
    assert not (builtin / "alpha").exists() and not (builtin / ".backup").exists()
    data = json.loads((builtin / "beta.json").read_text(encoding="utf-8"))
    assert "schema_version" not in data, "拒写失败：清单已被改动"


def test_g8_rollback_removes_created_files(tmp_path):
    """回滚删掉迁移新建的源码文件与空目录，并把清单还原到 v1。"""
    tree = _copy_tree(tmp_path)
    builtin = tree / "json_examples"
    plan = build_plan(builtin, tree, None)
    _ts, backup_dirs = apply_plan(plan, lambda manifest: manifest.parent / ".backup")
    created = [w.path for m in plan.manifests for w in m.writes if w.action == "create"]
    assert created and all(p.is_file() for p in created)
    rollback(backup_dirs)
    assert all(not p.exists() for p in created)
    # 只删自己建的：工作区与源目录里的既有文件不受影响
    assert (tree / "tools" / "utility-crawlers" / "crawler.py").is_file()
    shutil.rmtree(tmp_path / "tree", ignore_errors=True)
