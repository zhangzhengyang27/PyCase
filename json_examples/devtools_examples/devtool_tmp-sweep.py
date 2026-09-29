"""临时清理：删除 mtime 超过 N 天的 .tmp/.log/.cache 文件。"""
import argparse
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    cutoff = time.time() - args.days * 86400

    freed = 0
    for p in Path(args.directory).rglob("*"):
        if (p.is_file() and p.suffix in {".tmp", ".log", ".cache"}
                and p.stat().st_mtime < cutoff):
            freed += p.stat().st_size
            print("清理:", p)
            if args.apply:
                p.unlink()
    print(f"{'已清理' if args.apply else '可清理'} {freed / 1024:.0f} KB")


if __name__ == "__main__":
    main()
