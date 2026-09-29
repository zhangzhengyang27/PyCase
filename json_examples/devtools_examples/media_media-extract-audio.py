"""提取音频：python xxx.py input.mp4 -o audio.mp3"""
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
    ap.add_argument("--bitrate", default="192k")
    args = ap.parse_args()
    src = Path(args.input)
    dest = Path(args.output or src.with_suffix(".mp3"))
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-vn",
                        "-c:a", "libmp3lame", "-b:a", args.bitrate, str(dest)],
                       capture_output=True, text=True)
    print(f"提取完成 -> {dest}（{dest.stat().st_size // 1024} KB）" if r.returncode == 0
          else "失败: " + (r.stderr.strip().splitlines()[-1] if r.stderr else str(r.returncode)))


if __name__ == "__main__":
    main()
