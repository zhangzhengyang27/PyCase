"""文件监听：轮询 mtime，变更即提示。"""
import argparse
import time
from pathlib import Path


def snapshot(d):
    return {p: p.stat().st_mtime for p in d.rglob("*") if p.is_file()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--duration", type=float, default=10, help="监听秒数")
    args = ap.parse_args()
    base = Path(args.directory)
    before = snapshot(base)
    deadline = time.monotonic() + args.duration
    print(f"监听 {base}（{args.duration}s）…")
    while time.monotonic() < deadline:
        time.sleep(args.interval)
        now = snapshot(base)
        for p in now.keys() - before.keys():
            print("新增:", p)
        for p in before.keys() - now.keys():
            print("删除:", p)
        for p in now.keys() & before.keys():
            if now[p] != before[p]:
                print("修改:", p)
        before = now


if __name__ == "__main__":
    main()
