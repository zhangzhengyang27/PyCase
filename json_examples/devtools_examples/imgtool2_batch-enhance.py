"""画质调整：python xxx.py <目录> --brightness 1.1 --contrast 1.15"""
import argparse
from pathlib import Path

from PIL import Image, ImageEnhance

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--brightness", type=float, default=1.0)
    ap.add_argument("--contrast", type=float, default=1.0)
    ap.add_argument("--saturation", type=float, default=1.0)
    args = ap.parse_args()

    out = Path(args.directory) / "enhanced"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = im.convert("RGB")
            if args.brightness != 1.0:
                im = ImageEnhance.Brightness(im).enhance(args.brightness)
            if args.contrast != 1.0:
                im = ImageEnhance.Contrast(im).enhance(args.contrast)
            if args.saturation != 1.0:
                im = ImageEnhance.Color(im).enhance(args.saturation)
            dest = out / p.name
            im.save(dest, quality=90)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
