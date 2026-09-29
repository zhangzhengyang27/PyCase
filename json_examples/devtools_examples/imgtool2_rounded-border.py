"""圆角边框：python xxx.py <目录> --radius 24 --border 3"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--radius", type=int, default=24)
    ap.add_argument("--border", type=int, default=0)
    args = ap.parse_args()
    out = Path(args.directory) / "styled"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = rounded(im.convert("RGB"), args.radius)
            if args.border:
                d = ImageDraw.Draw(im)
                d.rounded_rectangle([0, 0, im.width - 1, im.height - 1],
                                    radius=args.radius, outline="#ffffff", width=args.border)
            dest = out / (p.stem + ".png")
            im.save(dest)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
