"""去音轨：python xxx.py input.mp4"""
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
    args = ap.parse_args()
    src = Path(args.input)
    dest = src.with_name(src.stem + "_mute" + src.suffix)
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-an", "-c:v", "copy", str(dest)],
                       capture_output=True, text=True)
    print(f"静音版 -> {dest}" if r.returncode == 0 else "失败")


if __name__ == "__main__":
    main()
