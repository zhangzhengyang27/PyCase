"""比例裁剪：python xxx.py <目录> --ratio 16:9"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def center_crop(im, rw, rh):
    target = rw / rh
    w, h = im.size
    cur = w / h
    if cur > target:  # 太宽，裁左右
        new_w = int(h * target)
        box = ((w - new_w) // 2, 0, (w + new_w) // 2, h)
    else:             # 太高，裁上下
        new_h = int(w / target)
        box = (0, (h - new_h) // 2, w, (h + new_h) // 2)
    return im.crop(box)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--ratio", default="16:9")
    args = ap.parse_args()
    rw, rh = (int(x) for x in args.ratio.split(":"))

    out = Path(args.directory) / "cropped"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            cropped = center_crop(im.convert("RGB"), rw, rh)
            dest = out / (p.stem + ".jpg")
            cropped.save(dest, "JPEG", quality=88)
        print(f"{p.name} -> {dest.name} {cropped.size}")


if __name__ == "__main__":
    main()
