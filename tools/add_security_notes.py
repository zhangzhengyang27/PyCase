#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为含教学用示例凭据/注入演示的文件头部插入说明注释（幂等）。"""
import os

# 仓库根（脚本所在 tools/ 的上一级），FILES 中的路径相对仓库根
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = [
    "python-basics/课程资料-基础/第09周/MySQL与Python的交互源码/demo_1/example_1.py",
    "python-basics/课程资料-基础/第09周/MySQL与Python的交互源码/demo_1/example_2.py",
    "python-basics/课程资料-基础/第09周/MySQL与Python的交互源码/demo_1/example_3.py",
    "python-basics/课程资料-基础/第10周/新闻管理系统应用开发Redis源码/Step 2/vega/db/redis_db.py",
    "python-basics/课程资料-基础/第10周/Redis与Python的交互/demo_2/redis_db.py",
]
NOTE = "# 注意：本文件含教学用示例凭据/注入演示，均为虚构值，非真实密码，请勿用于生产环境。"

for rel in FILES:
    f = os.path.join(BASE, rel)
    if not os.path.exists(f):
        print("缺失:", rel)
        continue
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    if NOTE in content:
        print("已注释(跳过):", rel)
        continue
    lines = content.split("\n")
    at = 0
    if lines and lines[0].startswith("#!"):
        at = 1
        if len(lines) > 1 and (lines[1].startswith("# -*-") or lines[1].startswith("# coding")):
            at = 2
    lines.insert(at, NOTE)
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("已添加注释:", rel)
