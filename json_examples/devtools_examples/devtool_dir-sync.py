"""目录同步：源 → 目标 增量复制（新增/更新才拷贝）。"""
import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    src, dst = Path(args.src), Path(args.dst)

    copied = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        target = dst / rel
        if (target.exists() and target.stat().st_mtime >= f.stat().st_mtime
                and target.stat().st_size == f.stat().st_size):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        copied += 1
        print("+", rel)
    print(f"同步完成：新增/更新 {copied} 个文件")


if __name__ == "__main__":
    main()
