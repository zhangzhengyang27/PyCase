"""音量：python xxx.py input.mp4 --gain 1.5 | --normalize"""
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
    ap.add_argument("--gain", type=float, default=1.0, help="音量倍数")
    ap.add_argument("--normalize", action="store_true", help="loudnorm 响度归一化")
    args = ap.parse_args()
    src = Path(args.input)
    dest = src.with_name(src.stem + "_vol" + src.suffix)
    if args.normalize:
        af = "loudnorm=I=-16:TP=-1.5:LRA=11"
    else:
        af = f"volume={args.gain}"
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-af", af,
                        "-c:v", "copy", str(dest)], capture_output=True, text=True)
    print(f"完成 -> {dest}" if r.returncode == 0 else "失败: " + r.stderr[-120:])


if __name__ == "__main__":
    main()
