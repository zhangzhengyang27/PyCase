"""文本 diff：unified 风格输出。"""
import argparse
import difflib
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    args = ap.parse_args()
    a = Path(args.a).read_text(encoding="utf-8").splitlines()
    b = Path(args.b).read_text(encoding="utf-8").splitlines()
    diff = difflib.unified_diff(a, b, fromfile=args.a, tofile=args.b, lineterm="")
    changed = 0
    for line in diff:
        print(line)
        changed += line[:1] in "+-"
    print(f"变更行: {changed}")


if __name__ == "__main__":
    main()
