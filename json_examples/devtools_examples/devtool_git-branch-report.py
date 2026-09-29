"""Git 分支报告：按最近提交排序。"""
import argparse
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    args = ap.parse_args()
    if not Path(args.repo, ".git").exists():
        print("不是 git 仓库")
        return
    branches = git("-C", args.repo, "branch", "--format=%(committerdate:short)%09%(refname:short)").splitlines()
    rows = []
    for line in branches:
        date, _, name = line.partition("	")
        rows.append((date, name))
    for date, name in sorted(rows, reverse=True):
        print(f"{date[:19]}  {name}")
    print("（已合并分支可用 git branch --merged 查看，再 -d 清理）")


if __name__ == "__main__":
    main()
