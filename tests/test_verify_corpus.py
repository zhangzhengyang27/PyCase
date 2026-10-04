"""语料验证器分类口径测试——分类函数纯化（无 IO）后逐类钉死，防口径漂移。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from verify_corpus import classify, load_allowlist  # noqa: E402


def test_ok_with_stdout() -> None:
    assert classify(0, "hello\n", "", False, 0) == "OK"


def test_ok_with_artifacts() -> None:
    assert classify(0, "", "", False, 2) == "OK"


def test_empty_suspicious() -> None:
    assert classify(0, "", "", False, 0) == "EMPTY"


def test_needs_args_is_by_design() -> None:
    err = "usage: prog [-h] --x X\nprog: error: the following arguments are required: --x"
    assert classify(2, "", err, False, 0) == "NEEDS_ARGS"


def test_needs_data_missing_input_file() -> None:
    err = "Traceback (most recent call last):\nFileNotFoundError: [Errno 2] No such file or directory: 'data.csv'"
    assert classify(1, "", err, False, 0) == "NEEDS_DATA"


def test_import_error() -> None:
    err = "Traceback (most recent call last):\nModuleNotFoundError: No module named 'pandas'"
    assert classify(1, "", err, False, 0) == "IMPORT_ERROR"


def test_gui_block_on_timeout_with_tk_marker() -> None:
    assert classify(124, "", "  File \"tkinter/__init__.py\", line 1, in mainloop", True, 0) == "GUI_BLOCK"


def test_gui_block_on_timeout_via_source_imports() -> None:
    # turtle/pygame 弹窗型超时时 stderr 干净（事件循环静默驻留），必须回源码识别
    assert classify(124, "", "", True, 0, source="import turtle\nturtle.done()") == "GUI_BLOCK"
    assert classify(124, "", "", True, 0, source="import pygame\ndisplay.flip()") == "GUI_BLOCK"
    assert classify(124, "", "", True, 0, source="cv2.imshow('x', img)") == "GUI_BLOCK"


def test_timeout_without_gui_marker_is_real_hang() -> None:
    assert classify(124, "", "", True, 0, source="while True:\n    pass") == "TIMEOUT"


def test_error_is_default_for_crash() -> None:
    err = "Traceback (most recent call last):\nZeroDivisionError: division by zero"
    assert classify(1, "", err, False, 0) == "ERROR"


def test_allowlist_parses_comments_and_multiple_verdicts(tmp_path: Path) -> None:
    p = tmp_path / "allow.txt"
    p.write_text(
        "# 注释行\n\n"
        "topics_web-ip-lookup NEEDS_DATA 需外网\n"
        "topics_web-ip-lookup ERROR 需外网\n",
        encoding="utf-8",
    )
    table = load_allowlist(p)
    assert table == {"topics_web-ip-lookup": {"NEEDS_DATA", "ERROR"}}
