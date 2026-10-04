"""数据契约 v2 清单模块测试（B2-1）。

覆盖契约 §2.3 的每条校验规则与 §2.4 的 v1 兼容窗口：
校验必须 fail-visible（报告里能看到问题）而不是 fail-crash（整个 load 罢工）。
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.manifest_v2 import (  # noqa: E402
    SCHEMA_VERSION,
    entry_code,
    load_manifest,
    resolve_entry_file,
)


def _write_manifest(tmp: Path, payload: dict, name: str = "demo.json") -> Path:
    path = tmp / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _v2_entry(**over) -> dict:
    entry = {
        "id": "hello",
        "name": "hello.py",
        "title": "打招呼",
        "category": "topics",
        "tags": ["基础"],
        "description": "打印问候语",
        "requirements": ["requests"],
        "file": "demo/hello.py",
    }
    entry.update(over)
    return entry


class TestSchemaDetection:
    def test_v1_manifest_is_readable_with_warning(self, tmp_path):
        path = _write_manifest(
            tmp_path,
            {
                "name": "老集合",
                "examples": [{"id": "a", "name": "a.py", "code": "print(1)"}],
            },
        )
        m = load_manifest(path)
        assert m.is_v1 and m.schema_version == 1
        assert [i.code for i in m.report.warnings] == ["v1-legacy"]
        # v1 兼容期仍能取到内联代码
        assert entry_code(m.path, m.entries[0], tmp_path) == "print(1)"

    def test_v2_manifest_reads_real_file(self, tmp_path):
        (tmp_path / "demo").mkdir()
        (tmp_path / "demo" / "hello.py").write_text("print('hi')", encoding="utf-8")
        path = _write_manifest(
            tmp_path, {"schema_version": 2, "name": "新集合", "examples": [_v2_entry()]}
        )
        m = load_manifest(path)
        assert m.schema_version == SCHEMA_VERSION and not m.is_v1
        assert m.report.errors == []
        resolved = resolve_entry_file(m.path, m.entries[0], tmp_path)
        assert resolved == (tmp_path / "demo" / "hello.py")
        assert entry_code(m.path, m.entries[0], tmp_path) == "print('hi')"

    def test_future_schema_version_warns_but_loads(self, tmp_path):
        path = _write_manifest(
            tmp_path, {"schema_version": 9, "name": "未来", "examples": [_v2_entry()]}
        )
        m = load_manifest(path)
        assert m.schema_version == 9
        assert "schema-newer" in [i.code for i in m.report.warnings]
        assert len(m.entries) == 1


class TestValidation:
    def test_missing_id_rejects_entry(self, tmp_path):
        path = _write_manifest(
            tmp_path, {"schema_version": 2, "name": "x", "examples": [{"name": "a.py"}]}
        )
        m = load_manifest(path)
        assert m.entries == []
        assert [i.code for i in m.report.errors] == ["id-missing"]

    def test_duplicate_id_keeps_first(self, tmp_path):
        path = _write_manifest(
            tmp_path,
            {
                "schema_version": 2,
                "name": "x",
                "examples": [_v2_entry(), _v2_entry(name="b.py")],
            },
        )
        m = load_manifest(path)
        assert [e.name for e in m.entries] == ["hello.py"]
        assert "id-duplicate" in [i.code for i in m.report.warnings]

    def test_dirty_id_charset_warns_but_keeps(self, tmp_path):
        path = _write_manifest(
            tmp_path,
            {"schema_version": 2, "name": "x", "examples": [_v2_entry(id="中文 id")]},
        )
        m = load_manifest(path)
        assert len(m.entries) == 1
        assert "id-charset" in [i.code for i in m.report.warnings]

    @pytest.mark.parametrize("bad_name", ["", "  ", "a/b.py", "a\\b.py", ".."])
    def test_invalid_name_rejects_entry(self, tmp_path, bad_name):
        path = _write_manifest(
            tmp_path,
            {"schema_version": 2, "name": "x", "examples": [_v2_entry(name=bad_name)]},
        )
        m = load_manifest(path)
        assert m.entries == []
        assert [i.code for i in m.report.errors] == ["name-invalid"]

    def test_invalid_requirements_dropped_with_warning(self, tmp_path):
        path = _write_manifest(
            tmp_path,
            {
                "schema_version": 2,
                "name": "x",
                "examples": [
                    _v2_entry(requirements=["requests", "-e .", " ", "numpy>=1.2"])
                ],
            },
        )
        m = load_manifest(path)
        assert m.entries[0].requirements == ["requests", "numpy>=1.2"]
        assert (
            len([i for i in m.report.warnings if i.code == "requirements-invalid"]) == 2
        )

    def test_unknown_fields_are_preserved(self, tmp_path):
        path = _write_manifest(
            tmp_path,
            {
                "schema_version": 2,
                "name": "x",
                "examples": [_v2_entry(custom_field={"k": 1})],
            },
        )
        m = load_manifest(path)
        assert m.entries[0].extra == {"custom_field": {"k": 1}}


class TestPathBoundary:
    def test_parent_reference_inside_tree_is_allowed(self, tmp_path):
        """原位示例用 ../topics/… 指向集合树内的真实文件，这是合法形态。"""
        (tmp_path / "topics").mkdir()
        (tmp_path / "topics" / "x.py").write_text("print(2)", encoding="utf-8")
        (tmp_path / "json_examples").mkdir()
        path = _write_manifest(
            tmp_path / "json_examples",
            {
                "schema_version": 2,
                "name": "x",
                "examples": [_v2_entry(file="../topics/x.py")],
            },
        )
        m = load_manifest(path)
        assert resolve_entry_file(m.path, m.entries[0], tmp_path) == (
            tmp_path / "topics" / "x.py"
        )

    def test_escape_beyond_data_root_is_rejected(self, tmp_path):
        """file 解析到集合树之外必须拒绝——否则 file 是数据外泄通道。"""
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.py").write_text("print('secret')", encoding="utf-8")
        root = tmp_path / "tree"
        (root / "json_examples").mkdir(parents=True)
        path = _write_manifest(
            root / "json_examples",
            {
                "schema_version": 2,
                "name": "x",
                "examples": [_v2_entry(file="../../outside/secret.py")],
            },
        )
        m = load_manifest(path)
        assert resolve_entry_file(m.path, m.entries[0], root) is None
        # 取码回退到内联（此条没有），最终为 None，而不是读到外部文件
        assert entry_code(m.path, m.entries[0], root) is None

    def test_missing_file_falls_back_to_inline_code(self, tmp_path):
        path = _write_manifest(
            tmp_path,
            {
                "schema_version": 2,
                "name": "x",
                "examples": [_v2_entry(file="demo/gone.py", code="print(3)")],
            },
        )
        m = load_manifest(path)
        assert entry_code(m.path, m.entries[0], tmp_path) == "print(3)"


class TestRealData:
    """对着真实数据跑一遍：迁移后全部为 v2 且零错误。"""

    def test_shipped_collections_load_without_errors(self):
        manifests = [p for p in sorted((ROOT / "json_examples").glob("*.json")) if p.name != "facts.json"]
        assert len(manifests) == 14
        total = 0
        for path in manifests:
            m = load_manifest(path)
            assert (
                m.report.errors == []
            ), f"{path.name}: {[i.message for i in m.report.errors]}"
            assert not m.is_v1, f"{path.name} 仍是 v1，迁移未完成"
            assert all(e.file for e in m.entries), f"{path.name} 有条目缺 file"
            assert all(not e.code for e in m.entries), f"{path.name} 仍带内联 code"
            total += len(m.entries)
        assert total == 487
