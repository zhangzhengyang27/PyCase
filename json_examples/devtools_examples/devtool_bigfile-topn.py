"""大文件 TopN：python devtool_bigfile.py <目录> [--top 10]"""
import argparse
from pathlib import Path


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def main():
    ap = argparse.ArgumentParser(description="递归查找最大的 N 个文件")
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    files = [(f.stat().st_size, f) for f in Path(args.directory).rglob("*") if f.is_file()]
    files.sort(reverse=True)
    for size, p in files[: args.top]:
        print(f"{human(size):>10}  {p}")


if __name__ == "__main__":
    main()
