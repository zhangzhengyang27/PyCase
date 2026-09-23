"""统一日志配置。

在项目中统一使用 ``get_logger(__name__)`` 获取 logger，替换散落的 ``print``。
调用 ``configure_logging()`` 后日志会输出到控制台（可选持久化到文件）。
"""

from __future__ import annotations

import logging

LOGGER_NAME = "python_example_manager"


def get_logger(name: str = "") -> logging.Logger:
    """获取带模块前缀的 logger。"""
    full = f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME
    return logging.getLogger(full)


def configure_logging(level: int = logging.INFO, log_file: str | None = None) -> None:
    """配置根 logger：输出到控制台，可选追加到日志文件。"""
    root = logging.getLogger(LOGGER_NAME)
    if root.handlers:
        return  # 避免重复配置

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler: logging.Handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError:
            root.warning("无法创建日志文件：%s", log_file)

    root.setLevel(level)
