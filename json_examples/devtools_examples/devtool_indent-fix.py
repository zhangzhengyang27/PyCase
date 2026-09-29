"""缩进修复：Tab→4空格 + 行尾空白。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    for f in args.files:
        p = Path(f)
        lines = p.read_text(encoding="utf-8").split("\n")
        fixed = [ln.replace("\t", "    ").rstrip() for ln in lines]
        if fixed != lines:
            print("规范化:", p)
            if args.apply:
                p.write_text("\n".join(fixed), encoding="utf-8")


if __name__ == "__main__":
    main()
