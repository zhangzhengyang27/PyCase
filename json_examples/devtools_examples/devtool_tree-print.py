"""目录树：tree 命令复刻。"""
import argparse
from pathlib import Path


def walk(d: Path, prefix: str, depth: int, max_depth: int, ignores: set):
    if depth > max_depth:
        return
    entries = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name))
    entries = [e for e in entries if e.name not in ignores]
    for i, e in enumerate(entries):
        last = i == len(entries) - 1
        print(prefix + ("└── " if last else "├── ") + e.name + ("/" if e.is_dir() else ""))
        if e.is_dir():
            walk(e, prefix + ("    " if last else "│   "), depth + 1, max_depth, ignores)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--ignore", nargs="*", default=["node_modules", ".git", "__pycache__"])
    args = ap.parse_args()
    print(Path(args.directory).resolve().name + "/")
    walk(Path(args.directory), "", 1, args.depth, set(args.ignore))


if __name__ == "__main__":
    main()
