"""批量水印：python xxx.py <目录> --text '© 2026' --mode corner|tile"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--text", default="© 示例库")
    ap.add_argument("--mode", choices=["corner", "tile"], default="corner")
    ap.add_argument("--opacity", type=int, default=110)
    args = ap.parse_args()

    out = Path(args.directory) / "watermarked"
    out.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)
    except OSError:
        font = ImageFont.load_default()

    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        base = Image.open(p).convert("RGBA")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        if args.mode == "corner":
            d.text((base.width - 130, base.height - 40), args.text,
                   fill=(255, 255, 255, args.opacity), font=font)
        else:
            for y in range(0, base.height, 90):
                for x in range(0, base.width, 200):
                    d.text((x, y), args.text, fill=(255, 255, 255, args.opacity), font=font)
        result = Image.alpha_composite(base, layer).convert("RGB")
        dest = out / p.name
        result.save(dest, quality=90)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
