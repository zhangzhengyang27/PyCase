#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""处理剩余目录的命名规范化。用法：python3 renumber_remaining.py [--dry]

策略：
- 扁平化示例集（消除无意义嵌套子目录），连续 NN- 编号。
- 保留独立包/项目目录（__init__.py / setup.py / 明确项目结构）。
- 保留 pytest 约定文件（test_*）。
"""
import os, re, sys, shutil

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python-basics")
DRY = "--dry" in sys.argv

PROTECT_DIRS = {"mypackage", "StudentManagerSystem", "dbdb项目", "exercise",
                "txt", "接口自动化", "课程资料", "课程资料-基础"}
PROTECT_PREFIX = ("test_",)

def natural_key(s):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", s)]

def clean_title(filename):
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r"^hm_\d+_", "", stem)
    stem = re.sub(r"^my[-_]", "", stem)
    stem = re.sub(r"^\d+-", "", stem)
    return stem

def flatten_examples(src_dir, dst_dir, prefix_note=""):
    """把 src_dir 下的示例 .py 收集到 dst_dir（扁平），返回收集到的文件列表。"""
    collected = []
    for root, dirs, files in os.walk(src_dir):
        # 跳过受保护目录
        rel = os.path.relpath(root, src_dir)
        top = rel.split(os.sep)[0]
        if top in PROTECT_DIRS and root != src_dir:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            if f.startswith(PROTECT_PREFIX):
                continue
            collected.append(os.path.join(root, f))
    return collected

def renumber_single(dirpath, files):
    """对单目录内 files 连续 NN- 编号。"""
    files = sorted(files, key=lambda x: natural_key(os.path.splitext(x)[0]))
    for i, f in enumerate(files, 1):
        title = clean_title(f)
        newname = f"{i:02d}-{title}.py"
        old = os.path.join(dirpath, f)
        new = os.path.join(dirpath, newname)
        flag = "DRY" if DRY else "MV"
        print(f"  [{flag}] {f} -> {newname}")
        if not DRY:
            new = os.path.join(dirpath, newname)
            if os.path.exists(new):
                print(f"  [冲突] 目标已存在，跳过: {newname}")
                continue
            os.rename(old, new)

# ---------- 1. 11-模块和包：扁平化示例 ----------
print("\n########## 11-模块和包")
ch11 = os.path.join(BASE, "11-模块和包")
# 收集示例文件（排除受保护目录和已受保护前缀）
examples = []
for root, dirs, files in os.walk(ch11):
    # 拦截受保护子目录，不进入其子树
    dirs[:] = [d for d in dirs if d not in PROTECT_DIRS]
    for f in files:
        if f.endswith(".py") and not f.startswith(PROTECT_PREFIX):
            examples.append(os.path.join(root, f))
# 按自然序排序后，移到 ch11 顶层并编号
examples.sort(key=lambda p: natural_key(os.path.basename(p)))
for i, p in enumerate(examples, 1):
    title = clean_title(os.path.basename(p))
    newname = f"{i:02d}-{title}.py"
    flag = "DRY" if DRY else "MV"
    print(f"  [{flag}] {os.path.relpath(p, ch11)} -> {newname}")
    if not DRY:
        dst = os.path.join(ch11, newname)
        if os.path.abspath(p) != os.path.abspath(dst):
            if os.path.exists(dst):
                print(f"  [冲突] 目标已存在，跳过: {newname}")
                continue
            shutil.move(p, dst)

# ---------- 2. 13-数据科学 顶层散落 .py ----------
print("\n########## 13-数据科学 (顶层 .py)")
ch13 = os.path.join(BASE, "13-数据科学")
top_py = [f for f in os.listdir(ch13)
          if f.endswith(".py") and not f.startswith(PROTECT_PREFIX)]
renumber_single(ch13, top_py)

# ---------- 3. 15-并发 ----------
print("\n########## 15-并发")
ch15 = os.path.join(BASE, "15-并发")
py15 = [f for f in os.listdir(ch15)
        if f.endswith(".py") and not f.startswith(PROTECT_PREFIX)]
renumber_single(ch15, py15)

print("\n完成。" + (" (DRY 模式，未实际修改)" if DRY else ""))
