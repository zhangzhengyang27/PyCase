#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一 crawler/01-basics 与 02-intermediate/dynamic 的文件命名。
- 去掉重复/无序前缀，统一为连续 NN-标题.py
- 驼峰英文文件名转 snake_case（如 MozillaCookieJar -> mozilla_cookie_jar）
用法：python3 renumber_crawler.py [--dry]"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
DRY = "--dry" in sys.argv

DIRS = [
    "crawler/01-basics/requests",
    "crawler/01-basics/parsing",
    "crawler/01-basics/storage",
    "crawler/02-intermediate/dynamic",
]

def camel_to_snake(name):
    stem, ext = os.path.splitext(name)
    if not re.fullmatch(r"[A-Za-z0-9]+", stem):
        return None
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", stem)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower() + ext

def clean_title(filename):
    stem = os.path.splitext(filename)[0]
    # 先去掉前缀编号 1- 2- 等
    stem = re.sub(r"^\d+-", "", stem)
    # 驼峰转 snake（仅当主体全 ASCII 字母数字/连字符）
    snk = camel_to_snake(stem)
    if snk:
        stem = os.path.splitext(snk)[0]
    return stem

total = 0
for rel in DIRS:
    d = os.path.join(BASE, rel)
    if not os.path.isdir(d):
        continue
    def sort_key(fn):
        stem = os.path.splitext(fn)[0]
        m = re.search(r"(\d+)", stem)
        return (0, int(m.group(1))) if m else (1, stem.lower())
    files = sorted([f for f in os.listdir(d) if f.endswith(".py")], key=sort_key)
    print(f"\n########## {rel} ({len(files)} 个)")
    for i, f in enumerate(files, 1):
        title = clean_title(f)
        newname = f"{i:02d}-{title}.py"
        total += 1
        print(f"  [{'DRY' if DRY else 'MV'}] {f} -> {newname}")
        if not DRY:
            dst = os.path.join(d, newname)
            if os.path.exists(dst):
                print(f"  [冲突] 目标已存在，跳过: {dst}")
                continue
            os.rename(os.path.join(d, f), dst)
print(f"\n{'[DRY] ' if DRY else ''}共 {total} 个文件。")
