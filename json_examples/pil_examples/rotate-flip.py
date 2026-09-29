"""旋转与翻转：方向图的多种变换"""
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


# 生成 240x240 方向图：白底 + 蓝色箭头 + 红色圆点
img = Image.new("RGB", (240, 240), "white")
d = ImageDraw.Draw(img)
d.polygon([(120, 20), (200, 100), (150, 100), (150, 220), (90, 220), (90, 100), (40, 100)], fill=(30, 144, 255))
d.ellipse([100, 100, 140, 140], fill=(255, 80, 80))

fig, axes = plt.subplots(2, 3, figsize=(12, 8))
titles = ["原图", "旋转 45°", "旋转 45°+扩展画布", "水平翻转", "垂直翻转", "旋转 90°"]
images = [img,
          img.rotate(45),
          img.rotate(45, expand=True),
          img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
          img.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
          img.transpose(Image.Transpose.ROTATE_90)]
for ax, t, im in zip(axes.flat, titles, images):
    ax.imshow(im)
    ax.set_title(t)
    ax.axis("off")
plt.suptitle("旋转与翻转：expand 会扩展画布适应新角度")
plt.tight_layout()
plt.savefig("rotate-flip_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")