#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规范化文件名：驼峰/连字符命名的英文 .py 改为 snake_case；清理冗余 venv 副本。

用法：python3 rename_normalize.py [--apply]  （默认 dry-run，传 --apply 才实际执行）

规则（已与用户确认）：
- 保留中文文件名（如 01-代码.py、hm_01_输入.py 不动）
- 仅对【纯英文】驼峰文件名做 snake_case 转换（myFirstPython.py -> my_first_python.py）
- 连字符目录中的英文文件，驼峰转 snake_case
- 不处理含中文的文件名
- 抽象名（number.py/main.py）不改名（需人工理解上下文，避免误改）
- 删除 automation-test 下混入的 venv/ 虚拟环境副本（冗余，非教学代码）
"""
import os
import re
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 默认 dry-run，仅在传入 --apply 时实际执行
DRY = "--apply" not in sys.argv


def camel_to_snake(name):
    """将 CamelCase / lowerCamel 转 snake_case。仅当文件名主体全为 ASCII 字母数字时生效。"""
    stem, ext = os.path.splitext(name)
    if not re.fullmatch(r"[A-Za-z0-9]+", stem):
        return None  # 含非 ASCII（中文）或特殊符号，不动
    # 在大写前插下划线（连续大写缩写如 HTTPServer -> http_server 处理）
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", stem)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower() + ext


def walk_rename(root):
    plan = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        # 跳过 .venv 与被清理的 venv（automation-test 按路径段精确匹配）
        if os.path.basename(dirpath) == "venv" and "automation-test" in dirpath.split(os.sep):
            plan.append(("DELETE_VENV", dirpath))
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            new = camel_to_snake(fn)
            if new and new != fn:
                plan.append(("RENAME", os.path.join(dirpath, fn), os.path.join(dirpath, new)))
    return plan


def main():
    plan = walk_rename(BASE)
    for action, *paths in plan:
        if action == "DELETE_VENV":
            p = paths[0]
            size = "?"
            print(f"[删冗余venv] {p}")
            if not DRY:
                try:
                    shutil.rmtree(p)
                except OSError as e:
                    print(f"[错误] 删除失败: {p} ({e})")
        else:
            old, new = paths
            print(f"[改名] {old}\n    -> {new}")
            if not DRY:
                os.rename(old, new)
    print(f"\n{'[DRY-RUN] ' if DRY else ''}共 {len(plan)} 项操作。")


if __name__ == "__main__":
    main()
