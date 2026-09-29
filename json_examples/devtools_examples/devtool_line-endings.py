"""换行符规范化：CRLF→LF，Tab→4 空格。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--ext", nargs="*", default=[".py", ".js", ".ts", ".md"])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    fixed = 0
    for p in Path(args.directory).rglob("*"):
        if p.suffix not in args.ext or not p.is_file():
            continue
        raw = p.read_bytes()
        new = raw.replace(b"\r\n", b"\n").replace(b"\t", b"    ")
        if new != raw:
            print("规范化:", p)
            fixed += 1
            if args.apply:
                p.write_bytes(new)
    print(f"{'已修复' if args.apply else '可修复'} {fixed} 个文件")


if __name__ == "__main__":
    main()
