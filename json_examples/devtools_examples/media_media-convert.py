"""格式转换：python xxx.py input.mov [-o output.mp4]"""
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
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = Path(args.input)
    dest = Path(args.output or src.with_suffix(".mp4"))
    r = subprocess.run([FFMPEG, "-y", "-i", str(src),
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        "-c:a", "aac", "-b:a", "128k", str(dest)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"转换完成 -> {dest} ({dest.stat().st_size // 1024 // 1024} MB)")
    else:
        print("失败:", r.stderr.strip().splitlines()[-1] if r.stderr else r.returncode)


if __name__ == "__main__":
    main()
