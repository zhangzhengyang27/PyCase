"""裁剪：python xxx.py input.mp4 --start 00:00:10 --duration 30"""
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
    ap.add_argument("--start", default="00:00:00")
    ap.add_argument("--duration", type=float, default=10)
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = Path(args.input)
    dest = Path(args.output or src.with_name(src.stem + "_clip" + src.suffix))
    r = subprocess.run([FFMPEG, "-y", "-ss", args.start, "-i", str(src),
                        "-t", str(args.duration), "-c", "copy", str(dest)],
                       capture_output=True, text=True)
    print(f"裁剪完成 -> {dest}" if r.returncode == 0 else "失败: " + r.stderr[-120:])


if __name__ == "__main__":
    main()
