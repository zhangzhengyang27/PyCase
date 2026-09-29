"""Git 统计：shortlog + numstat。"""
import subprocess
from collections import defaultdict


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout

by_author = defaultdict(lambda: [0, 0, 0])
shortlog = git("log", "--format=%an|%h")
for line in shortlog.splitlines():
    author = line.split("|")[0]
    by_author[author][0] += 1
numstat = git("log", "--numstat", "--format=")
for line in numstat.splitlines():
    if not line.strip():
        continue
    add, dele, _ = line.split("\t")
    author = None
    for a in by_author:
        if a:
            author = a  # 简化：不计归属粒度
            break
    if author:
        by_author[author][1] += int(add or 0) if add.isdigit() else 0
        by_author[author][2] += int(dele or 0) if dele.isdigit() else 0
for author, (commits, add, dele) in sorted(by_author.items(), key=lambda x: -x[1][0]):
    print(f"{author:<16} 提交 {commits:>4}  +{add} -{dele}")
