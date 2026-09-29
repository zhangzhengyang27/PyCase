"""空目录清扫：自底向上删除空目录。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    base = Path(args.directory)

    removed = 0
    for d in sorted(base.rglob("*"), key=lambda p: -len(p.parts)):
        if d.is_dir() and not any(d.iterdir()):
            print("空目录:", d)
            if args.apply:
                d.rmdir()
            removed += 1
    print(f"{'已删除' if args.apply else '发现'} {removed} 个空目录")


if __name__ == "__main__":
    main()
