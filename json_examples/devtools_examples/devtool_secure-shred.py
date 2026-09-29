"""文件粉碎：随机覆写 3 遍 + 改名 + 删除。"""
import argparse
import os
from pathlib import Path


def shred(path: Path, passes: int = 3):
    size = path.stat().st_size
    with open(path, "r+b") as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())
    path.rename(path.with_name(path.name + ".shredded"))
    path.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--passes", type=int, default=3)
    args = ap.parse_args()
    for f in args.files:
        p = Path(f)
        if p.exists():
            shred(p, args.passes)
            print("已粉碎:", f)


if __name__ == "__main__":
    main()
