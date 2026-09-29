"""九宫格切图：3x3 批量切片"""
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
# 尝试设置中文字体（找不到时中文显示为方块但不影响运行）
try:
    from matplotlib import font_manager
    _zh_fonts = [f.name for f in font_manager.fontManager.ttflist if any(
        k in f.name for k in ("PingFang", "Heiti", "Songti", "Hiragino", "YaHei", "SimHei", "Arial Unicode"))]
    if _zh_fonts:
        plt.rcParams["font.sans-serif"] = [_zh_fonts[0]]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass


# 程序化生成 300x300 编号渐变图
W = 300
xx = np.linspace(0, 255, W, dtype=np.uint8)
img = Image.fromarray(np.tile(xx, (W, 1)), "L").convert("RGB")
d = ImageDraw.Draw(img)
for i in range(9):
    r, c = divmod(i, 3)
    d.rectangle([c * 100, r * 100, c * 100 + 98, r * 100 + 98], outline=(255, 255, 255), width=4)

step = W // 3
tiles = []
for r in range(3):
    for c in range(3):
        tiles.append(img.crop((c * step, r * step, (c + 1) * step, (r + 1) * step)))

fig, axes = plt.subplots(3, 3, figsize=(9, 9))
for ax, tile in zip(axes.flat, tiles):
    ax.imshow(tile)
    ax.axis("off")
plt.suptitle("九宫格切图：3x3 切片")
plt.tight_layout()
plt.savefig("nine-grid-split_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")