"""格式转换：python xxx.py <目录> --to webp"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--to", choices=["png", "jpg", "webp"], default="webp")
    ap.add_argument("--quality", type=int, default=85)
    args = ap.parse_args()
    fmt = "JPEG" if args.to in ("jpg", "jpeg") else args.to.upper()

    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = im.convert("RGB") if fmt == "JPEG" else im
            dest = p.with_suffix("." + args.to)
            im.save(dest, fmt, quality=args.quality)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
