from PIL import Image, ImageDraw
"""霓虹发光：边缘 + 高斯模糊叠光"""
from PIL import Image, ImageFilter, ImageChops
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


# 程序化生成简单图形
W, H = 360, 240
img = Image.new("RGB", (W, H), (10, 10, 25))
d = ImageDraw.Draw(img)
d.ellipse([70, 50, 290, 190], outline=(255, 255, 255), width=3)
d.line([(60, 40), (300, 200)], fill=(255, 255, 255), width=3)

# 提取轮廓（发光源）
edges = img.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda p: 255 if p > 40 else 0)
glow_src = Image.merge("RGB", [edges] * 3)

# 多层高斯模糊叠加发光
glow = Image.new("RGB", (W, H), (0, 0, 0))
for radius, color in [(12, (30, 40, 255)), (7, (120, 140, 255)), (3, (230, 240, 255))]:
    layer = glow_src.filter(ImageFilter.GaussianBlur(radius))
    layer = ImageChops.multiply(layer, Image.new("RGB", (W, H), color))
    glow = ImageChops.add(glow, layer)

# 合成
result = ImageChops.add(img, glow)

plt.figure(figsize=(9, 6))
plt.imshow(result)
plt.axis("off")
plt.title("霓虹发光效果")
plt.savefig("glow-effect_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
result.save("glow_demo.png")