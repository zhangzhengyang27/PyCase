from PIL import Image, ImageDraw
"""ImageDraw 几何绘制：基础图形全家福"""
from PIL import Image, ImageDraw
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


img = Image.new("RGB", (420, 320), "white")
d = ImageDraw.Draw(img)

d.line([(20, 40), (120, 40)], fill=(0, 0, 0), width=3)
d.rectangle([150, 20, 260, 90], outline=(30, 144, 255), width=3)
d.ellipse([290, 20, 400, 90], outline=(255, 80, 80), width=3)
d.arc([20, 120, 130, 230], start=30, end=300, fill=(0, 160, 80), width=3)
d.chord([160, 120, 270, 230], start=0, end=120, fill=(255, 215, 0), outline=(0, 0, 0))
d.pieslice([300, 120, 410, 230], start=0, end=270, fill=(200, 100, 255), outline=(0, 0, 0))
d.polygon([(20, 260), (80, 300), (60, 240), (120, 260)], fill=(100, 200, 255))
d.rounded_rectangle([170, 250, 300, 310], radius=20, fill=(255, 150, 100))

plt.figure(figsize=(9, 7))
plt.imshow(img)
plt.axis("off")
plt.title("ImageDraw 几何绘制")
plt.savefig("draw-shapes_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
img.save("draw_shapes_demo.png")