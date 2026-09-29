"""视频压缩：python xxx.py input.mp4 --crf 26 --preset fast"""
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
    ap.add_argument("--crf", type=int, default=26, help="18 高质量 ~ 28 高压缩")
    ap.add_argument("--preset", default="fast")
    args = ap.parse_args()
    src = Path(args.input)
    dest = src.with_name(src.stem + "_compressed.mp4")
    before = src.stat().st_size
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-c:v", "libx264",
                        "-preset", args.preset, "-crf", str(args.crf),
                        "-c:a", "aac", "-b:a", "96k", str(dest)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        after = dest.stat().st_size
        print(f"{before // 1024 // 1024} MB -> {after // 1024 // 1024} MB "
              f"（{100 - after * 100 // before}% 缩减）")
    else:
        print("失败:", r.stderr.strip().splitlines()[-1] if r.stderr else r.returncode)


if __name__ == "__main__":
    main()
