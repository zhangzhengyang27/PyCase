"""图片报告：目录内图片尺寸/格式/体积一览。"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    total = 0
    print(f"{'文件':<30}{'尺寸':<12}{'格式':<6}{'体积':>9}")
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            kb = p.stat().st_size / 1024
            total += kb
            print(f"{p.name[:28]:<30}{f'{im.width}×{im.height}':<12}{im.format:<6}{kb:>7.0f}KB")
    print(f"合计 {total:.0f} KB")


if __name__ == "__main__":
    main()
