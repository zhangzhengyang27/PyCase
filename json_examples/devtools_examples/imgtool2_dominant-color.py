"""主色调：缩图 + 量化取出现最多的颜色。"""
import argparse
from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    im = Image.open(args.image).convert("RGB")
    im.thumbnail((80, 80))
    counts = {}
    for px in im.getdata():
        quant = (px[0] // 16 * 16, px[1] // 16 * 16, px[2] // 16 * 16)
        counts[quant] = counts.get(quant, 0) + 1
    total = sum(counts.values())
    for (r, g, b), n in sorted(counts.items(), key=lambda x: -x[1])[:args.top]:
        print(f"#{r:02x}{g:02x}{b:02x}  {100 * n / total:5.1f}%  {'█' * int(100 * n / total / 4)}")


if __name__ == "__main__":
    main()
