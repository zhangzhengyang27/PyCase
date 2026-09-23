#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对剩余单层章节统一连续编号 NN-标题.py，去掉 hm_/my-/pachong 等前缀。
不建子目录（主题单一）。用法：python3 renumber.py [--dry]"""
import os, re, sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python-basics")
DRY = "--dry" in sys.argv

CHAPTERS = [
    "02-if条件语句", "03-while&for 循环语句", "08-文件操作",
    "10-异常处理", "12-爬虫示例", "16-标准库", "18-日志记录",
]

def clean_title(filename):
    stem = os.path.splitext(filename)[0]
    # 去掉常见前缀
    stem = re.sub(r"^hm_\d+_", "", stem)
    stem = re.sub(r"^my[-_]", "", stem)
    stem = re.sub(r"^pachong", "爬虫示例", stem)
    stem = re.sub(r"^\d+-", "", stem)  # 去掉 11-、09- 等原编号
    return stem

for ch in CHAPTERS:
    chdir = os.path.join(BASE, ch)
    files = sorted([f for f in os.listdir(chdir) if f.endswith(".py")],
                   key=lambda x: os.path.splitext(x)[0])
    print(f"\n########## {ch} ({len(files)} 个)")
    for i, f in enumerate(files, 1):
        title = clean_title(f)
        newname = f"{i:02d}-{title}.py"
        flag = "DRY" if DRY else "MV"
        print(f"  [{flag}] {f} -> {newname}")
        if not DRY:
            dst = os.path.join(chdir, newname)
            if os.path.exists(dst):
                print(f"  [冲突] 目标已存在，跳过: {dst}")
                continue
            os.rename(os.path.join(chdir, f), dst)
