"""拼贴墙：python xxx.py <目录> --cols 4 --cell 240"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=240)
    ap.add_argument("-o", default="contact_sheet.jpg")
    args = ap.parse_args()

    imgs = []
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() in SUPPORTED and p.is_file():
            im = Image.open(p).convert("RGB")
            im.thumbnail((args.cell, args.cell))
            imgs.append((p.name, im))
    if not imgs:
        print("无图片")
        return
    rows = (len(imgs) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (args.cols * (args.cell + 8) + 8, rows * (args.cell + 26) + 8), "#181c24")
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(imgs):
        x = 8 + (i % args.cols) * (args.cell + 8)
        y = 8 + (i // args.cols) * (args.cell + 26)
        sheet.paste(im, (x + (args.cell - im.width) // 2, y + (args.cell - im.height) // 2))
        d.text((x, y + args.cell + 4), name[:28], fill="#cfd8e3")
    sheet.save(args.o, quality=88)
    print(f"拼贴 {len(imgs)} 张 -> {args.o}")


if __name__ == "__main__":
    main()
