from PIL import Image, ImageDraw
"""图像差异检测：找不同"""
from PIL import Image, ImageChops
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


# 程序化生成两张"几乎相同"的图
W, H = 320, 220
base = Image.new("RGB", (W, H), (240, 240, 245))
d = ImageDraw.Draw(base)
for i in range(0, W, 40):
    d.line([(i, 0), (i, H)], fill=(200, 200, 210), width=1)
for j in range(0, H, 40):
    d.line([(0, j), (W, j)], fill=(200, 200, 210), width=1)
d.rectangle([40, 40, 120, 100], fill=(255, 200, 100))
d.ellipse([200, 60, 280, 140], fill=(120, 220, 255))

img2 = base.copy()
d2 = ImageDraw.Draw(img2)
d2.rectangle([40, 40, 120, 100], fill=(255, 80, 80))     # 颜色不同
d2.ellipse([200, 60, 280, 140], fill=(120, 220, 255))    # 原样
d2.polygon([(150, 150), (170, 190), (130, 190)], fill=(0, 160, 0))  # 新增

diff = ImageChops.difference(base, img2).convert("L")
# 差异区域放大显示
mark = base.copy()
md = ImageDraw.Draw(base)
arr = np.asarray(diff)
ys, xs = np.where(arr > 20)
if len(xs):
    md.rectangle([xs.min() - 6, ys.min() - 6, xs.max() + 6, ys.max() + 6],
                 outline=(255, 0, 0), width=3)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, im, t in zip(axes, [base, img2, mark], ["图 A", "图 B", "差异高亮"]):
    ax.imshow(im)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.savefig("image-diff_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")