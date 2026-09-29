"""正则测试：pattern + 样本 → 匹配详情。"""
import argparse
import re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("sample")
    args = ap.parse_args()
    rx = re.compile(args.pattern)
    matches = list(rx.finditer(args.sample))
    if not matches:
        print("无匹配")
        return
    for m in matches:
        print(f"[{m.start()}:{m.end()}] {m.group()!r}")
        for gi, g in enumerate(m.groups() or [], 1):
            if g is not None:
                print(f"   组{gi}: {g!r}")
    print(f"共 {len(matches)} 处匹配")


if __name__ == "__main__":
    main()
