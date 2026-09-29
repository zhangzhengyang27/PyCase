"""合成 GIF：python xxx.py frame_*.png 所在目录 -o out.gif --fps 8"""
import argparse
from pathlib import Path

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("-o", default="out.gif")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--width", type=int, default=480)
    args = ap.parse_args()
    frames = []
    for p in sorted(Path(args.directory).glob("*.png")):
        im = Image.open(p).convert("RGB")
        scale = args.width / im.width
        frames.append(im.resize((args.width, int(im.height * scale))))
    if not frames:
        print("无 PNG 帧")
        return
    duration = int(1000 / args.fps)
    frames[0].save(args.o, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0)
    print(f"已合成 {len(frames)} 帧 -> {args.o}")


if __name__ == "__main__":
    main()
