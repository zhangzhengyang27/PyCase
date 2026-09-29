"""图片批量压缩：等比缩放 + 质量控制。"""
import argparse
from pathlib import Path

from PIL import Image


def compress(path: Path, out: Path, max_side: int, quality: int) -> None:
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, max_side / max(w, h))
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        im.save(out, "JPEG", quality=quality, optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--max-side", type=int, default=1280)
    parser.add_argument("--quality", type=int, default=82)
    args = parser.parse_args()

    out_dir = Path(args.directory) / "compressed"
    out_dir.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).glob("*")):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"} or not p.is_file():
            continue
        out = out_dir / (p.stem + ".jpg")
        compress(p, out, args.max_side, args.quality)
        print(f"{p.name}: {p.stat().st_size // 1024}KB -> {out.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
