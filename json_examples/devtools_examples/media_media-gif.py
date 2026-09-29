"""视频转 GIF：python xxx.py clip.mp4 --start 5 --duration 3 --width 480"""
import argparse
from pathlib import Path

import shutil
import subprocess
import sys

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
if not FFMPEG:
    print("未找到 ffmpeg（brew install ffmpeg / apt install ffmpeg）")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--duration", type=float, default=3)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("-o", default="out.gif")
    args = ap.parse_args()
    vf = (f"fps={args.fps},scale={args.width}:-1:flags=lanczos,"
          "split[a][b];[a]palettegen[p];[b][p]paletteuse")
    r = subprocess.run([FFMPEG, "-y", "-ss", str(args.start), "-t", str(args.duration),
                        "-i", args.input, "-vf", vf, args.o], capture_output=True, text=True)
    if r.returncode == 0:
        size = Path(args.o).stat().st_size // 1024
        print(f"已生成 {args.o}（{size} KB）")
    else:
        print("失败:", r.stderr[-120:])


if __name__ == "__main__":
    main()
