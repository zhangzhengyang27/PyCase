"""RGB 通道分离与合并"""
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


# 程序化生成 300x300 三色圆
img = Image.new("RGB", (300, 300), "black")
d = ImageDraw.Draw(img)
d.ellipse([50, 50, 250, 250], fill=(255, 0, 0))
d.ellipse([80, 80, 220, 220], fill=(0, 255, 0))
d.ellipse([110, 110, 190, 190], fill=(0, 0, 255))

r, g, b = img.split()

# 把单通道染回对应颜色
def tint(channel, color):
    black = Image.new("RGB", channel.size, (0, 0, 0))
    black.paste(color, (0, 0), channel)
    return black

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(img)
axes[0, 0].set_title("原图")
axes[0, 1].imshow(tint(r, (255, 0, 0)))
axes[0, 1].set_title("R 通道")
axes[1, 0].imshow(tint(g, (0, 255, 0)))
axes[1, 0].set_title("G 通道")
axes[1, 1].imshow(tint(b, (0, 0, 255)))
axes[1, 1].set_title("B 通道")
for ax in axes.flat:
    ax.axis("off")
plt.tight_layout()
plt.savefig("color-channels_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")