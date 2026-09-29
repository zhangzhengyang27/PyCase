"""批量替换：python xxx.py 目录 旧文本 新文本 --ext .py .md"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--ext", nargs="*", default=[".py", ".md", ".txt"])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed = 0
    for p in Path(args.directory).rglob("*"):
        if p.suffix not in args.ext or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if args.old not in text:
            continue
        n = text.count(args.old)
        print(f"{p}: {n} 处")
        changed += n
        if args.apply:
            p.write_text(text.replace(args.old, args.new), encoding="utf-8")
    print(f"{'已替换' if args.apply else '可替换'} {changed} 处")


if __name__ == "__main__":
    main()
