"""通用工具函数。"""

import re
from pathlib import Path


def find_repo_root(start_path: Path) -> Path:
    """从起始路径向上查找仓库根目录。

    优先通过 .git 目录定位真正的仓库根；若未找到 .git，则退而求其次
    使用 requirements.txt 作为项目根标记。
    """
    current = start_path.resolve()

    # 第一遍：优先查找 .git
    candidate = current
    while candidate.parent != candidate:
        if (candidate / ".git").exists():
            return candidate
        candidate = candidate.parent

    # 第二遍：未找到 .git 时回退到 requirements.txt
    candidate = current
    while candidate.parent != candidate:
        if (candidate / "requirements.txt").exists():
            return candidate
        candidate = candidate.parent

    return start_path.resolve()


def is_python_file(path: Path) -> bool:
    """判断是否为有效的 Python 文件。"""
    return path.is_file() and path.suffix == ".py" and not path.name.startswith(".")


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符。"""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本并在末尾添加省略号。"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."
