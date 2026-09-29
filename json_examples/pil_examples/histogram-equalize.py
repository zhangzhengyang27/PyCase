"""直方图与均衡化：低对比度图像增强"""
from PIL import Image, ImageDraw, ImageOps
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


# 程序化生成低对比度图
W, H = 300, 300
v = np.linspace(60, 130, W, dtype=np.uint8)
img = Image.fromarray(np.tile(v, (H, 1)), "L")
d = ImageDraw.Draw(img)
d.ellipse([80, 80, 220, 220], outline=255, width=3)

eq = ImageOps.equalize(img)

fig, axes = plt.subplots(2, 2, figsize=(10, 9))
axes[0, 0].imshow(img, cmap="gray")
axes[0, 0].set_title("原图（低对比度）")
axes[0, 0].axis("off")
axes[0, 1].hist(np.asarray(img).ravel(), bins=64, color="#2e86de")
axes[0, 1].set_title("原图直方图（集中在窄范围）")
axes[1, 0].imshow(eq, cmap="gray")
axes[1, 0].set_title("均衡化后")
axes[1, 0].axis("off")
axes[1, 1].hist(np.asarray(eq).ravel(), bins=64, color="#e17055")
axes[1, 1].set_title("均衡化直方图（分布更均匀）")
plt.tight_layout()
plt.savefig("histogram-equalize_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")