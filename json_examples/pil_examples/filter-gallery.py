from PIL import Image, ImageDraw
"""滤镜效果画廊：8 种内置滤镜对比"""
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


# 程序化生成测试图：几何图形 + 渐变背景
W, H = 300, 300
xx = np.linspace(0, 255, W, dtype=np.uint8)
bg = Image.fromarray(np.tile(xx, (H, 1)), "L").convert("RGB")
d = ImageDraw.Draw(bg)
d.ellipse([40, 40, 260, 260], fill=(255, 220, 100), outline=(255, 80, 80), width=6)
d.rectangle([90, 90, 210, 210], outline=(40, 120, 255), width=6)
d.line([(30, 270), (270, 30)], fill=(80, 200, 80), width=8)

filters = [
    ("原图", None),
    ("BLUR 模糊", ImageFilter.BLUR),
    ("CONTOUR 轮廓", ImageFilter.CONTOUR),
    ("DETAIL 细节", ImageFilter.DETAIL),
    ("EMBOSS 浮雕", ImageFilter.EMBOSS),
    ("EDGE_ENHANCE 边缘增强", ImageFilter.EDGE_ENHANCE),
    ("FIND_EDGES 查找边缘", ImageFilter.FIND_EDGES),
    ("SHARPEN 锐化", ImageFilter.SHARPEN),
    ("SMOOTH 平滑", ImageFilter.SMOOTH),
]

fig, axes = plt.subplots(3, 3, figsize=(12, 12))
for ax, (t, f) in zip(axes.flat, filters):
    im = bg.filter(f) if f else bg
    ax.imshow(im)
    ax.set_title(t, fontsize=10)
    ax.axis("off")
plt.suptitle("Pillow 内置滤镜效果")
plt.tight_layout()
plt.savefig("filter-gallery_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")