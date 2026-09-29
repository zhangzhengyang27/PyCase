"""GIF 拆帧：python xxx.py anim.gif -o frames"""
import argparse
from pathlib import Path

from PIL import Image, ImageSequence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gif")
    ap.add_argument("-o", default="frames")
    args = ap.parse_args()
    out = Path(args.o)
    out.mkdir(exist_ok=True)
    with Image.open(args.gif) as im:
        for i, frame in enumerate(ImageSequence.Iterator(im)):
            frame.convert("RGB").save(out / f"frame_{i:03d}.png")
    print(f"已导出 {i + 1} 帧 -> {out}")


if __name__ == "__main__":
    main()
