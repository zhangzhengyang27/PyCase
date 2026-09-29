"""快速查找：名称正则 + 类型过滤。"""
import argparse
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", help="名称正则")
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--type", choices=["f", "d"], default="f")
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()
    rx = re.compile(args.pattern, re.IGNORECASE)

    count = 0
    for p in Path(args.directory).rglob("*"):
        if len(p.parts) > 2 and any(x in p.parts for x in ("node_modules", ".git")):
            continue
        if (p.is_file() if args.type == "f" else p.is_dir()) and rx.search(p.name):
            print(p)
            count += 1
            if count >= args.limit:
                break
    print(f"共 {count} 个（上限 {args.limit}）")


if __name__ == "__main__":
    main()
