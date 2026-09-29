"""批量重命名：默认预览，--apply 执行。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--prefix", default="file")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(p for p in Path(args.directory).iterdir() if p.is_file())
    plan = [(p, p.with_name(f"{args.prefix}_{i:03d}{p.suffix}")) for i, p in enumerate(files, 1)]
    for old, new in plan:
        print(f"{old.name} -> {new.name}")
    if args.apply:
        for old, new in plan:
            old.rename(new)
        print(f"已重命名 {len(plan)} 个")
