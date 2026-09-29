from PIL import Image, ImageDraw
"""自定义卷积核：3x3 锐化 / 浮雕 / 模糊"""
from PIL import Image, ImageFilter
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


# 程序化生成测试图
W, H = 280, 280
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
d.ellipse([40, 40, 240, 240], fill=(255, 170, 60), outline=(120, 60, 200), width=5)
for i in range(0, 280, 20):
    d.line([(i, 0), (i, 280)], fill=(200, 200, 220), width=1)
    d.line([(0, i), (280, i)], fill=(200, 200, 220), width=1)

kernels = [
    ("锐化", (0, -1, 0, -1, 5, -1, 0, -1, 0), 1.0),
    ("浮雕", (-1, -1, 0, -1, 0, 1, 0, 1, 1), 1.0),
    ("高斯模糊", (1, 2, 1, 2, 4, 2, 1, 2, 1), 16.0),
]

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(img)
axes[0, 0].set_title("原图")
axes[0, 0].axis("off")
for ax, (t, kern, scale) in zip(axes.flat[1:], kernels):
    out = img.filter(ImageFilter.Kernel((3, 3), kern, scale=scale, offset=128 if "浮雕" in t else 0))
    ax.imshow(out)
    ax.set_title(f"{t}（3x3 卷积核）")
    ax.axis("off")
plt.tight_layout()
plt.savefig("custom-kernel_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")