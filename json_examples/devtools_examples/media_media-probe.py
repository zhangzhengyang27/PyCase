import shutil
import subprocess
import sys

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
if not FFMPEG:
    print("未找到 ffmpeg（brew install ffmpeg / apt install ffmpeg）")
    sys.exit(1)

def probe(path):
    """ffprobe 取时长/码率/分辨率（JSON）。"""
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True)
    import json as _json
    return _json.loads(r.stdout or "{}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("media", nargs="+")
    args = ap.parse_args()
    for path in args.media:
        info = probe(path)
        fmt = info.get("format", {})
        v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
        print(f"{path}")
        print(f"  时长 {float(fmt.get('duration', 0)):.1f}s | "
              f"{v.get('width', '?')}×{v.get('height', '?')} | "
              f"{v.get('codec_name', '?')} | {int(fmt.get('bit_rate', 0)) // 1024} kbps")


if __name__ == "__main__":
    main()
