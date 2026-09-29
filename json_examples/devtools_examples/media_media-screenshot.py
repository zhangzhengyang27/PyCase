"""截图：单帧 --at 00:00:30，或 --every 5 批量截帧。"""
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
    ap.add_argument("--at", default="00:00:05", help="单帧时间点")
    ap.add_argument("--every", type=float, default=0, help="每 N 秒一帧（批量模式）")
    ap.add_argument("-o", default="frame.png")
    args = ap.parse_args()
    if args.every > 0:
        r = subprocess.run([FFMPEG, "-y", "-i", args.input, "-vf",
                            f"fps=1/{args.every}", "shot_%03d.png"], capture_output=True, text=True)
        print("批量截帧完成" if r.returncode == 0 else "失败")
    else:
        r = subprocess.run([FFMPEG, "-y", "-ss", args.at, "-i", args.input,
                            "-frames:v", "1", args.o], capture_output=True, text=True)
        print(f"截图 -> {args.o}" if r.returncode == 0 else "失败")


if __name__ == "__main__":
    main()
