#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将按周命名的目录改为按内容语义命名。用法：python3 rename_weeks.py [--dry]"""
import os, sys, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
DRY = "--dry" in sys.argv

# (旧绝对路径, 新目录名)
RENAMES = [
    # automation-test
    (os.path.join(BASE, "automation-test/第34~35周"),
     "web与接口自动化实战"),
    (os.path.join(BASE, "automation-test/第34~35周/10 后台管理"),
     "Django后台管理实战"),
    # crawler 补充
    (os.path.join(BASE, "crawler/课程资料-补充"),
     "课程补充示例"),
    (os.path.join(BASE, "crawler/课程资料-补充/第14周"),
     "requests入门补充"),
    (os.path.join(BASE, "crawler/课程资料-补充/第15周"),
     "爬虫常用技术与实战"),
    (os.path.join(BASE, "crawler/课程资料-补充/第16周"),
     "Scrapy与自动化爬虫"),
    (os.path.join(BASE, "crawler/课程资料-补充/第17~18周"),
     "验证码与反爬实战"),
    # web-framework
    (os.path.join(BASE, "web-framework/Django/第26周"),
     "模板与入门"),
    (os.path.join(BASE, "web-framework/Django/第27周"),
     "ORM与表单"),
    (os.path.join(BASE, "web-framework/Flask/第24周"),
     "入门与模板"),
    (os.path.join(BASE, "web-framework/Flask/第25周"),
     "在线问答系统实战"),
]

# 从深到浅排序，避免父目录先改名导致子路径失效
RENAMES_SORTED = sorted(RENAMES, key=lambda p: p[0].count(os.sep), reverse=True)

for old, new in RENAMES_SORTED:
    if not os.path.exists(old):
        print(f"[跳过] 不存在: {old}")
        continue
    parent = os.path.dirname(old)
    dst = os.path.join(parent, new)
    flag = "DRY" if DRY else "MV"
    print(f"[{flag}] {old}\n      -> {dst}")
    if not DRY:
        # 目标不存在才移动；若存在则报错提示
        if os.path.exists(dst):
            print(f"    [警告] 目标已存在，跳过: {dst}")
        else:
            shutil.move(old, dst)

print("\n完成。" + (" (DRY 模式)" if DRY else ""))
