"""批量缩放：python xxx.py <目录> --max-side 1600"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--max-side", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=85)
    args = ap.parse_args()

    out = Path(args.directory) / "resized"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = im.convert("RGB")
            scale = min(1.0, args.max_side / max(im.size))
            if scale < 1.0:
                im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
            dest = out / (p.stem + ".jpg")
            im.save(dest, "JPEG", quality=args.quality, optimize=True)
        print(f"{p.name} -> {dest.name} ({im.size[0]}×{im.size[1]})")


if __name__ == "__main__":
    main()
