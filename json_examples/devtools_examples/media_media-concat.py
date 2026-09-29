"""合并：python xxx.py a.mp4 b.mp4 c.mp4 -o merged.mp4"""
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
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", default="merged.mp4")
    args = ap.parse_args()
    if len(args.inputs) < 2:
        print("至少两个输入")
        return
    import tempfile
    lst = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    for p in args.inputs:
        lst.write(f"file '{Path(p).resolve()}'\n")
    lst.close()
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
                        "-i", lst.name, "-c", "copy", args.o],
                       capture_output=True, text=True)
    Path(lst.name).unlink()
    print(f"合并 {len(args.inputs)} 段 -> {args.o}" if r.returncode == 0 else "失败（编码不一致时先统一转码）")


if __name__ == "__main__":
    main()
