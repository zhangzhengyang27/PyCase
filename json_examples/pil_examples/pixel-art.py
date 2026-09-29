"""像素风马赛克：降采样 + 最近邻放大"""
from PIL import Image
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


# 程序化生成 400x400 渐变圆
W = 400
xx, yy = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, W))
r = np.sqrt(xx ** 2 + yy ** 2)
hue = np.arctan2(yy, xx)
# HSV 转简易 RGB 彩虹圆
hsv = np.stack([(hue + np.pi) / (2 * np.pi), np.ones_like(r), 1 - r], axis=-1)
import colorsys
rgb = np.zeros((W, W, 3))
for i in range(0, W, 25):
    for j in range(0, W, 25):
        h, s, v = hsv[i, j]
        rgb[i:i + 25, j:j + 25] = colorsys.hsv_to_rgb(h, s, v)
img = Image.fromarray((rgb * 255).astype(np.uint8))

# 马赛克：先缩到 40x40 再放大回 400x400
pixel = img.resize((40, 40), Image.Resampling.NEAREST).resize((W, W), Image.Resampling.NEAREST)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(img)
axes[0].set_title("原图 400x400")
axes[0].axis("off")
axes[1].imshow(pixel)
axes[1].set_title("像素风 40x40 马赛克")
axes[1].axis("off")
plt.tight_layout()
plt.savefig("pixel-art_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")