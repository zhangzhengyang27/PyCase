"""图像融合：Image.blend 权重渐变"""
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


# 生成两张对比图
W, H = 300, 300
img1 = Image.new("RGB", (W, H), (30, 144, 255))
img2 = Image.new("RGB", (W, H), (255, 165, 0))
d1 = ImageDraw.Draw(img1)
d2 = ImageDraw.Draw(img2)
d1.ellipse([60, 60, 240, 240], fill=(255, 255, 255))
d2.polygon([(150, 40), (260, 240), (40, 240)], fill=(255, 255, 255))

alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
fig, axes = plt.subplots(1, 5, figsize=(16, 4))
for ax, a in zip(axes, alphas):
    blended = Image.blend(img1, img2, a)
    ax.imshow(blended)
    ax.set_title(f"alpha={a:.2f}")
    ax.axis("off")
plt.suptitle("Image.blend 图像融合")
plt.tight_layout()
plt.savefig("image-blend_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")