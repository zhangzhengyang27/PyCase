"""Markdown TOC：把 # 标题生成目录并打印。"""
import argparse
import re
from pathlib import Path


def anchor(text):
    return re.sub(r"[^\w\u4e00-\u9fff- ]", "", text).strip().replace(" ", "-").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    args = ap.parse_args()
    lines = Path(args.file).read_text(encoding="utf-8").splitlines()
    for line in lines:
        m = re.match(r"^(#{1,4})\s+(.+)", line)
        if m:
            depth, title = len(m.group(1)), m.group(2).strip()
            print("  " * (depth - 1) + f"- [Markdown 目录生成](#{anchor(title)})")


if __name__ == "__main__":
    main()
