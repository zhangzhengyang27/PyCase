#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将课程资料（按周组织的 Python 代码）融合进当前项目。

用法：
  python3 merge_courseware.py --src <课程资料目录> [--dry]

- 仅 Python 代码为主，28~33 周前端资产(.vue/.js/.css/.html/.json)也保留
- 去重基准：按文件内容 sha256，与现有项目或已复制文件相同的跳过
- 目录组织：并入现有结构 + 新建 web-framework/、automation-test/、web-frontend/

注意：原来源目录 /Users/xiaoye/Desktop/20260803/00.课程资料 已融合完毕并删除，
本脚本仅供将来再次融合同类资料时使用，源目录通过 --src 指定。

映射规则（按周次）：
  01~11周   -> python-basics/课程资料-基础/<原名>
  12周      -> web-frontend/第12周/<原名>  (HTML/CSS 源码 + 图片)
  13~23周   -> crawler/课程资料-补充/<原名>
  24~25周   -> web-framework/Flask/<原名>
  26~27周   -> web-framework/Django/<原名>
  28~33周   -> web-frontend/<周次>/<原名>  (含前端资产)
  34~35周   -> automation-test/<原名>
  19~22/36周 -> python-basics/13-数据科学/课程资料/<原名>
"""

import hashlib
import os
import shutil
import sys

# 目标目录：脚本所在目录的上一级（即项目根）
DST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = None  # 通过 --src 指定

# 需要保留的非 .py 资产扩展名（仅前端周次使用）
FRONTEND_EXT = {".vue", ".js", ".css", ".html", ".json", ".ts", ".jsx", ".tsx"}

# 数据科学周次(.ipynb 等)保留的扩展名
DATA_EXT = {".ipynb", ".csv", ".xlsx", ".py", ".json", ".md", ".txt"}

# 排除的噪声/二进制扩展名
NOISE_EXT = {
    ".pyc", ".dll", ".pyd", ".exe", ".zip", ".rar", ".msi", ".crx",
    ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp3",
    ".mp4", ".sqlite3", ".sql", ".cfg", ".ini", ".sublime-settings",
    ".tar", ".gz", ".tgz", ".dat", ".bin", ".vbs", ".xlsx", ".ipynb",
}

# 周次 -> 目标相对目录
WEEK_MAP = {
    "第01周": ("python-basics/课程资料-基础", False),
    "第02周": ("python-basics/课程资料-基础", False),
    "第03周": ("python-basics/课程资料-基础", False),
    "第04周": ("python-basics/课程资料-基础", False),
    "第05周": ("python-basics/课程资料-基础", False),
    "第06周": ("python-basics/课程资料-基础", False),
    "第07周": ("python-basics/课程资料-基础", False),
    "第08周": (None, False),
    "第09周": ("python-basics/课程资料-基础", False),
    "第10周": ("python-basics/课程资料-基础", False),
    "第11周": ("python-basics/课程资料-基础", False),
    "第12周": ("web-frontend/第12周", True),  # HTML/CSS 前端源码(补录)
    "第13周": ("crawler/课程资料-补充", False),
    "第14周": ("crawler/课程资料-补充", False),
    "第15周": ("crawler/课程资料-补充", False),
    "第16周": ("crawler/课程资料-补充", False),
    "第17~18周": ("crawler/课程资料-补充", False),
    "第19周": ("python-basics/13-数据科学/课程资料", "data"),
    "第20周": ("python-basics/13-数据科学/课程资料", "data"),
    "第21周": ("python-basics/13-数据科学/课程资料", "data"),
    "第22周": ("python-basics/13-数据科学/课程资料", "data"),
    "第23周": ("crawler/课程资料-补充", False),
    "第24周": ("web-framework/Flask", False),
    "第25周": ("web-framework/Flask", False),
    "第26周": ("web-framework/Django", False),
    "第27周": ("web-framework/Django", False),
    "第28周": ("web-frontend/第28周", True),
    "第29周": ("web-frontend/第29周", True),
    "第30周": ("web-frontend/第30周", True),
    "第31周": ("web-frontend/第31周", True),
    "第32周": ("web-frontend/第32周", True),
    "第33周": ("web-frontend/第33周", True),
    "第34~35周": ("automation-test", False),
    "第36周": ("python-basics/13-数据科学/课程资料", "data"),
}


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_copy2(src_file, dst_file, src_hash, dry):
    """带覆盖保护的复制：目标已存在且内容相同→跳过；内容不同→不覆盖。
    返回 "ok"(已/将复制) / "dup"(目标同内容已存在) / "conflict"(目标不同内容已存在)。"""
    if os.path.exists(dst_file):
        try:
            if file_hash(dst_file) == src_hash:
                return "dup"
        except OSError:
            pass
        return "conflict"
    if not dry:
        shutil.copy2(src_file, dst_file)
    return "ok"


def build_existing_hashes():
    """索引当前项目所有 .py 的 hash，用于去重。"""
    hashes = set()
    for root, _, files in os.walk(DST):
        for fn in files:
            if fn.endswith(".py"):
                try:
                    hashes.add(file_hash(os.path.join(root, fn)))
                except OSError:
                    pass
    return hashes


def main():
    dry = "--dry" in sys.argv
    existing = build_existing_hashes()
    copied_hashes = set(existing)  # 已存在或已复制的 hash
    stats = {"copied": 0, "skipped_dup": 0, "skipped_conflict": 0,
             "skipped_noise": 0, "skipped_excluded": 0}

    for week in sorted(os.listdir(SRC)):
        src_week = os.path.join(SRC, week)
        if not os.path.isdir(src_week) or week not in WEEK_MAP:
            continue
        target_rel, mode = WEEK_MAP[week]
        if target_rel is None:
            stats["skipped_excluded"] += 1
            print(f"[排除] {week} (非 Python / HTML-CSS)")
            continue

        for root, dirs, files in os.walk(src_week):
            # 跳过 __pycache__
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                # 根据 mode 决定保留的扩展名集合
                if mode == "data":
                    keep = ext == ".py" or ext in DATA_EXT
                else:
                    keep = ext == ".py" or (mode and ext in FRONTEND_EXT)
                if keep:
                    src_file = os.path.join(root, fn)
                    try:
                        h = file_hash(src_file)
                    except OSError:
                        continue
                    if h in copied_hashes:
                        stats["skipped_dup"] += 1
                        continue
                    # 目标路径：保留原始相对子目录结构
                    rel_sub = os.path.relpath(root, src_week)
                    dst_dir = os.path.join(DST, target_rel, week, rel_sub)
                    os.makedirs(dst_dir, exist_ok=True)
                    dst_file = os.path.join(dst_dir, fn)
                    res = safe_copy2(src_file, dst_file, h, dry)
                    if res == "conflict":
                        print(f"[警告] 目标已存在且内容不同，跳过: {dst_file}")
                        stats["skipped_conflict"] += 1
                        continue
                    if res == "dup":
                        stats["skipped_dup"] += 1
                        continue
                    copied_hashes.add(h)
                    stats["copied"] += 1
                elif ext in NOISE_EXT:
                    stats["skipped_noise"] += 1
                else:
                    stats["skipped_noise"] += 1

    print("\n=== 融合统计 ===")
    print(f"已复制(去重后): {stats['copied']}")
    print(f"跳过(内容重复): {stats['skipped_dup']}")
    print(f"跳过(目标冲突): {stats['skipped_conflict']}")
    print(f"跳过(噪声/二进制): {stats['skipped_noise']}")
    print(f"排除周次: {stats['skipped_excluded']}")
    if dry:
        print("\n[DRY-RUN] 未实际写入文件。")


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry" in args
    # 精确解析 --src（避免 --srcxxx 误匹配），支持 "--src <路径>" 与 "--src=<路径>"
    for i, a in enumerate(args):
        if a == "--src":
            SRC = args[i + 1] if i + 1 < len(args) else None
        elif a.startswith("--src="):
            SRC = a.split("=", 1)[1]
    if not SRC:
        print("错误：必须通过 --src <课程资料目录> 指定源目录。")
        print("用法：python3 merge_courseware.py --src /path/to/课程资料 [--dry]")
        sys.exit(1)
    if not os.path.isdir(SRC):
        print(f"错误：源目录不存在：{SRC}")
        sys.exit(1)
    main()
