"""代码统计：按扩展名汇总行数。"""
import argparse
from collections import defaultdict
from pathlib import Path


def count_file(p):
    code = comment = blank = 0
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s:
            blank += 1
        elif s.startswith(("#", "//")):
            comment += 1
        else:
            code += 1
    return code, comment, blank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    stats = defaultdict(lambda: [0, 0, 0, 0])
    for p in Path(args.directory).rglob("*"):
        if p.is_file() and p.suffix in {".py", ".js", ".ts", ".vue", ".mjs"} and "node_modules" not in p.parts:
            c, cm, b = count_file(p)
            s = stats[p.suffix]
            s[0] += c; s[1] += cm; s[2] += b; s[3] += 1
    print(f"{'类型':<6}{'文件':>5}{'代码':>8}{'注释':>8}{'空行':>8}")
    for ext, (c, cm, b, n) in sorted(stats.items(), key=lambda x: -x[1][0]):
        print(f"{ext:<6}{n:>5}{c:>8}{cm:>8}{b:>8}")


if __name__ == "__main__":
    main()
