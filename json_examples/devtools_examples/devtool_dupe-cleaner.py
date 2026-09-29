"""重复文件清理：默认只报告，--delete 执行清理。"""
import argparse
import hashlib
from collections import defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--delete", action="store_true", help="删除重复（保留每组第一个）")
    args = ap.parse_args()

    groups = defaultdict(list)
    for p in Path(args.directory).rglob("*"):
        if p.is_file() and p.stat().st_size < 512 * 1024 * 1024:
            groups[hashlib.md5(p.read_bytes()).hexdigest()].append(p)

    freed = 0
    for paths in groups.values():
        if len(paths) < 2:
            continue
        print("重复组:", [str(p) for p in paths])
        for dup in paths[1:]:
            freed += dup.stat().st_size
            if args.delete:
                dup.unlink()
    print(f"{'已删除' if args.delete else '可释放'}: {freed / 1024:.0f} KB")


if __name__ == "__main__":
    main()
