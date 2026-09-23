#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验融合完整性：源目录应纳入的文件是否全部已存在于目标。

用法：python3 verify_merge.py --src <课程资料目录>
"""
import argparse, hashlib, os, sys

DST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = {".vue", ".js", ".css", ".html", ".json", ".ts", ".jsx", ".tsx"}
DATA = {".ipynb", ".csv", ".xlsx", ".py", ".json", ".md", ".txt"}
# 扫描时排除的目录（两侧均生效）
EXCLUDE_DIRS = {".venv", ".git", ".idea", "_archive", "__pycache__", ".json_examples_cache"}

WEEK_MAP = {
    "第01周": ("b", False), "第02周": ("b", False), "第03周": ("b", False),
    "第04周": ("b", False), "第05周": ("b", False), "第06周": ("b", False),
    "第07周": ("b", False), "第08周": (None, False), "第09周": ("b", False),
    "第10周": ("b", False), "第11周": ("b", False), "第12周": ("w", True),
    "第13周": ("c", False), "第14周": ("c", False), "第15周": ("c", False),
    "第16周": ("c", False), "第17~18周": ("c", False), "第19周": ("d", "data"),
    "第20周": ("d", "data"), "第21周": ("d", "data"), "第22周": ("d", "data"),
    "第23周": ("c", False), "第24周": ("f", False), "第25周": ("f", False),
    "第26周": ("j", False), "第27周": ("j", False), "第28周": ("wf", True),
    "第29周": ("wf", True), "第30周": ("wf", True), "第31周": ("wf", True),
    "第32周": ("wf", True), "第33周": ("wf", True), "第34~35周": ("a", False),
    "第36周": ("d", "data"),
}


def h(p):
    hl = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            hl.update(c)
    return hl.hexdigest()


def parse_args():
    ap = argparse.ArgumentParser(description="校验融合完整性：源目录应纳入的文件是否全部已存在于目标。")
    ap.add_argument("--src", required=True, help="源课程资料目录（按周组织）")
    return ap.parse_args()


# 先校验参数，再执行扫描
args = parse_args()
SRC = args.src
if not os.path.isdir(SRC):
    print(f"错误：源目录不存在：{SRC}")
    sys.exit(1)

# 目标已存在 hash
dst_hashes = set()
for r, ds, fs in os.walk(DST):
    ds[:] = [d for d in ds if d not in EXCLUDE_DIRS]
    for fn in fs:
        e = os.path.splitext(fn)[1].lower()
        if e == ".py" or e in (FRONTEND | DATA):
            try:
                dst_hashes.add(h(os.path.join(r, fn)))
            except OSError:
                pass

# 源应纳入
src_hashes = set()
missing = []
for wk in os.listdir(SRC):
    sp = os.path.join(SRC, wk)
    if not os.path.isdir(sp) or wk not in WEEK_MAP:
        continue
    _, mode = WEEK_MAP[wk]
    if wk == "第08周":
        continue
    for r, ds, fs in os.walk(sp):
        ds[:] = [d for d in ds if d not in EXCLUDE_DIRS]
        for fn in fs:
            e = os.path.splitext(fn)[1].lower()
            if mode == "data":
                keep = e == ".py" or e in DATA
            else:
                keep = e == ".py" or (mode and e in FRONTEND)
            if keep:
                fp = os.path.join(r, fn)
                try:
                    hh = h(fp)
                except OSError:
                    continue
                src_hashes.add(hh)
                if hh not in dst_hashes:
                    missing.append(fp)

print("源应纳入唯一文件数:", len(src_hashes))
print("目标已包含(与源交集)数:", len(dst_hashes & src_hashes))
print("遗漏(源有但目标无)数:", len(missing))
if missing:
    print("遗漏样例:", missing[:5])
else:
    print("✅ 全部应纳入文件均已存在于目标，无遗漏。")
