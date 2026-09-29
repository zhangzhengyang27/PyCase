"""音频压缩：python xxx.py input.wav --bitrate 96k"""
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
    ap.add_argument("--bitrate", default="128k")
    ap.add_argument("--codec", choices=["libmp3lame", "aac", "opus"], default="libmp3lame")
    args = ap.parse_args()
    src = Path(args.input)
    ext = {"libmp3lame": ".mp3", "aac": ".m4a", "opus": ".opus"}[args.codec]
    dest = src.with_name(src.stem + "_small" + ext)
    before = src.stat().st_size // 1024
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-c:a", args.codec,
                        "-b:a", args.bitrate, str(dest)], capture_output=True, text=True)
    after = dest.stat().st_size // 1024 if dest.exists() else 0
    print(f"{before} KB -> {after} KB ({dest.name})" if r.returncode == 0 else "失败")


if __name__ == "__main__":
    main()
