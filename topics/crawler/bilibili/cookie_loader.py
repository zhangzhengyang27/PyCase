"""BILI_COOKIE 统一加载：优先读环境变量，其次读 .env，缺失则友好提示。

配合 bilibili_login.py 使用：先运行登录助手写入 .env，再跑爬虫。
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

_ENV_HINT = (
    "未找到 BILI_COOKIE。\n"
    "请先运行登录助手获取 Cookie：\n"
    "    source .venv/bin/activate\n"
    "    python bilibili_login.py\n"
    "登录成功后 Cookie 会自动写入 .env，无需手动设置。"
)

# 登录态关键字段，缺失时 B站 多数接口会返回 -101/未登录
_REQUIRED_KEYS = ("SESSDATA",)


def _check_cookie(cookie: str) -> None:
    """校验 Cookie 基本完整性，缺失关键字段时给出明确告警但不强制退出。"""
    missing = [k for k in _REQUIRED_KEYS if f"{k}=" not in cookie]
    if missing:
        print(
            f"警告：Cookie 可能不完整，缺少关键字段 {missing}。\n"
            "部分接口可能返回未登录状态，建议重新运行 bilibili_login.py 获取。",
            file=sys.stderr,
        )


def load_cookie() -> str:
    """返回有效的 BILI_COOKIE，缺失时打印提示并退出程序。"""
    cookie = (os.environ.get("BILI_COOKIE") or os.getenv("BILI_COOKIE") or "").strip()
    if not cookie:
        print(_ENV_HINT, file=sys.stderr)
        sys.exit(1)
    _check_cookie(cookie)
    return cookie
