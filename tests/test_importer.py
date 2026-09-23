"""导入核心（app/importer.py）的单元测试：纯函数 + tmp 目录全流程，不依赖网络。"""

import json
import re
from pathlib import Path

from app.importer import (
    IMPORT_TO_PKG,
    build_source_modules,
    derive_tags,
    ensure_unique_id,
    extract_imports,
    guess_requirements,
    import_directory,
    read_requirements,
    slugify,
    spec_from_file,
)


# --------------------------------------------------------------------- 纯函数


def test_slugify_charset():
    assert slugify("hello world.py") == "hello_world.py"
    assert re.fullmatch(r"topics_+a\.py", slugify("topics/算法/代码/a.py"))
    assert slugify("keep-1_2.3") == "keep-1_2.3"


def test_extract_imports_ast_semantics():
    code = "\n".join(
        [
            "import os, sys",
            "import numpy as np",
            "from PIL import Image",
            "from .helpers import x",  # 相对导入不计
            "from config.settings import y",  # 取顶层 config
            "import dubious_escape\\d",  # 语法错误整体跳过
        ]
    )
    # 最后一行语法错误 → 整个文件 parse 失败返回空集（保守：不猜依赖）
    assert extract_imports(code) == set()
    assert extract_imports("import os\nimport numpy as np\nfrom PIL import Image\n") == {
        "os",
        "numpy",
        "PIL",
    }


def test_derive_tags_from_dirs_and_modules():
    tags = derive_tags(["topics", "algorithms", "code", "a.py"], {"numpy", "requests"})
    # 中间目录段（除首段分类与尾段文件名）都算标签
    assert "algorithms" in tags and "code" in tags
    assert "数据科学" in tags and "网络" in tags
    assert "topics" not in tags


def test_guess_requirements_excludes_available_local_and_maps_pkg():
    local = {"common", "utils"}
    available = {"os", "requests", "numpy"}
    is_avail = lambda m: m in available  # noqa: E731
    code = "import os\nimport requests\nimport cv2\nimport common.helpers\nimport notapkg\n"
    pkgs = guess_requirements(code, local, is_available=is_avail)
    # cv2 → opencv-python；notapkg 无映射回退自身；os/requests 可用；common 本地
    assert pkgs == ["opencv-python", "notapkg"]
    assert IMPORT_TO_PKG["cv2"] == "opencv-python"


def test_guess_requirements_deterministic_and_dedup():
    is_avail = lambda m: False  # noqa: E731
    code = "import zlib\nimport cv2\nimport cv2\n"
    assert guess_requirements(code, set(), is_available=is_avail) == ["opencv-python", "zlib"]


def test_read_requirements_handles_utf16_and_versions(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_bytes("flask>=2.0\n# comment\nopencv-python\n-e .\n".encode("utf-16"))
    assert read_requirements(tmp_path) == ["flask", "opencv-python"]


def test_ensure_unique_id_suffix():
    seen = {"a"}
    assert ensure_unique_id("a", seen) == "a_2"
    assert ensure_unique_id("a", seen) == "a_3"
    assert ensure_unique_id("b", seen) == "b"
    assert seen == {"a", "a_2", "a_3", "b"}


def test_build_source_modules_includes_stems_packages_and_ancestors(tmp_path):
    (tmp_path / "pkg" / "sub").mkdir(parents=True)
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "sub" / "tool_a.py").write_text("", encoding="utf-8")
    mods = build_source_modules(tmp_path)
    assert {"pkg", "sub", "tool_a"} <= mods


# --------------------------------------------------------------------- 目录导入流程


def make_source(tmp_path: Path) -> Path:
    src = tmp_path / "my_repo"
    (src / "demos" / "basic").mkdir(parents=True)
    (src / "demos" / "basic" / "hello.py").write_text(
        'import cv2\nprint("hi")\n' + "# " + "x" * 40 + "\n", encoding="utf-8"
    )
    (src / "demos" / "empty.py").write_text("", encoding="utf-8")
    (src / "demos" / "README.md").write_text("# 演示集合\n", encoding="utf-8")
    (src / "demos" / "requirements.txt").write_text("flask\n", encoding="utf-8")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "junk.py").write_text("print('skip')\n", encoding="utf-8")
    return src


def test_import_directory_full_flow(tmp_path):
    src = make_source(tmp_path)
    is_avail = lambda m: m == "cv2"  # noqa: E731  cv2 已装 → 不猜；hello.py 无其他第三方
    payload = import_directory(src, "我的示例", existing_ids={"hello"}, is_available=is_avail)
    assert payload["name"] == "我的示例"
    assert payload["stats"] == {"scanned": 3, "imported": 1, "skipped": 2}
    ids = [ex["id"] for ex in payload["examples"]]
    # 空文件被跳过；__pycache__ 不导入
    assert "demos_empty.py" not in ids and "junk" not in str(ids)
    hello = next(ex for ex in payload["examples"] if "hello" in ex["id"])
    assert hello["category"] == "user"
    assert "dir" not in hello  # 用户集合不写 dir（单文件物化）
    assert hello["description"] == "演示集合"  # 同目录 README 首行
    assert "flask" in hello["requirements"]  # 声明依赖保留
    assert hello["tags"] == ["basic"]  # 中间目录段标签（首段/文件名除外）
    # 跳过原因：空文件 + 缓存目录
    reasons = {(s["file"], s["reason"]) for s in payload["skipped"]}
    assert ("demos/empty.py", "空文件") in reasons
    assert ("__pycache__/junk.py", "位于缓存/隐藏目录") in reasons


def test_import_directory_dedupes_against_existing_ids(tmp_path):
    src = tmp_path / "src"
    (src / "demos").mkdir(parents=True)
    # 相对路径 demos/hello.py → id demos_hello.py，与 existing 冲突两次
    (src / "demos" / "hello.py").write_text("print(1)\n", encoding="utf-8")
    payload = import_directory(
        src, "dup", existing_ids={"demos_hello.py"}, is_available=lambda m: True
    )
    ids = [ex["id"] for ex in payload["examples"]]
    assert ids == ["demos_hello.py_2"]


def test_spec_from_file_merges_declared_and_guessed(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("import cv2\nprint(1)\n", encoding="utf-8")
    (src / "requirements.txt").write_text("flask==2.0\n", encoding="utf-8")
    spec = spec_from_file(src / "a.py", src, set(), is_available=lambda m: False)
    assert spec["requirements"] == ["flask", "opencv-python"]  # 声明在前、猜测去重追加
    assert json.dumps(spec)  # 可 JSON 序列化
