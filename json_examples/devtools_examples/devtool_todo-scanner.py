"""TODO 扫描：TODO/FIXME/HACK/XXX 全库清单。"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

RX = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[:：]?\s*(.*)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    by_file = defaultdict(list)
    for p in Path(args.directory).rglob("*"):
        if p.suffix not in {".py", ".js", ".ts", ".vue", ".mjs"} or "node_modules" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = RX.search(line)
            if m:
                by_file[str(p)].append((i, m.group(1), m.group(2)[:50]))
    for f, marks in sorted(by_file.items()):
        print(f)
        for i, kind, text in marks:
            print(f"  L{i} [{kind}] {text}")
    print(f"共 {sum(len(v) for v in by_file.values())} 处未完成标记")


if __name__ == "__main__":
    main()
