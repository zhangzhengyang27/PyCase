"""批量转码：python xxx.py <目录> --crf 24"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import shutil
import subprocess
import sys

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
if not FFMPEG:
    print("未找到 ffmpeg（brew install ffmpeg / apt install ffmpeg）")
    sys.exit(1)


def convert(p, crf):
    dest = p.with_suffix(".mp4")
    if dest.exists():
        return f"跳过（已存在）: {dest.name}"
    r = subprocess.run([FFMPEG, "-y", "-i", str(p), "-c:v", "libx264",
                        "-crf", str(crf), "-c:a", "aac", str(dest)],
                       capture_output=True, text=True)
    return f"{'✓' if r.returncode == 0 else '✗'} {p.name} -> {dest.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--crf", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    videos = [p for p in Path(args.directory).iterdir()
              if p.suffix.lower() in {".mov", ".avi", ".mkv", ".webm", ".flv"} and p.is_file()]
    with ThreadPoolExecutor(args.workers) as pool:
        for line in pool.map(lambda p: convert(p, args.crf), videos):
            print(line)


if __name__ == "__main__":
    main()
