"""批量重命名：dry-run 预览 + 执行。"""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="目录内文件批量重命名")
    parser.add_argument("directory", nargs="?", default=".", help="目标目录")
    parser.add_argument("--prefix", default="file", help="新文件名前缀")
    parser.add_argument("--ext", default="", help="仅处理指定扩展名，如 .txt")
    parser.add_argument("--apply", action="store_true", help="真正执行（默认只预览）")
    args = parser.parse_args()

    target = Path(args.directory)
    files = sorted(p for p in target.iterdir()
                   if p.is_file() and (not args.ext or p.suffix == args.ext))
    plan = []
    for i, p in enumerate(files, 1):
        new_name = f"{args.prefix}_{i:03d}{p.suffix}"
        plan.append((p, p.with_name(new_name)))

    for old, new in plan:
        print(f"{old.name} -> {new.name}")
    if args.apply:
        for old, new in plan:
            old.rename(new)
        print(f"已重命名 {len(plan)} 个文件")
    else:
        print(f"（预览模式，共 {len(plan)} 个文件；加 --apply 执行）")


if __name__ == "__main__":
    main()
