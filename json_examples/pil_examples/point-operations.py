"""点运算：反色 / 自动对比度 / 直方图均衡化 / 色调分离"""
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


# 程序化生成低对比度渐变图（模拟欠曝照片）
W, H = 300, 300
v = np.linspace(60, 120, W, dtype=np.uint8)  # 低动态范围
low = Image.fromarray(np.tile(v, (H, 1)), "L")
low = low.convert("RGB")

d = ImageDraw.Draw(low)
d.ellipse([80, 80, 220, 220], outline=(255, 255, 255), width=3)
d.line([(0, 150), (300, 150)], fill=(255, 255, 255), width=2)
d.line([(150, 0), (150, 300)], fill=(255, 255, 255), width=2)

results = {
    "原图": low,
    "反色 invert": ImageOps.invert(low),
    "自动对比度": ImageOps.autocontrast(low, cutoff=2),
    "直方图均衡": ImageOps.equalize(low),
    "色调分离 4 级": ImageOps.posterize(low, 4),
    "灰度化": low.convert("L"),
}

fig, axes = plt.subplots(2, 3, figsize=(13, 9))
for ax, (t, im) in zip(axes.flat, results.items()):
    ax.imshow(im, cmap="gray" if im.mode == "L" else None)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.savefig("point-operations_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")