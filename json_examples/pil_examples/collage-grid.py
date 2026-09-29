"""缩略图墙：多图拼接 2x3"""
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


# 程序化生成 6 张不同色调的渐变图
thumbs = []
for hue_base in range(0, 360, 60):
    W, H = 120, 120
    v = np.linspace(0, 255, W, dtype=np.uint8)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    # 简化的 HSV 色调色板
    r = int(128 + 127 * np.sin(np.radians(hue_base)))
    g = int(128 + 127 * np.sin(np.radians(hue_base + 120)))
    b = int(128 + 127 * np.sin(np.radians(hue_base + 240)))
    d.ellipse([10, 10, 110, 110], fill=(r, g, b))
    thumb = img.resize((100, 100), Image.Resampling.LANCZOS)
    thumbs.append(thumb)

wall = Image.new("RGB", (100 * 3 + 40, 100 * 2 + 30), "white")
for i, t in enumerate(thumbs):
    r, c = divmod(i, 3)
    wall.paste(t, (10 + c * 110, 10 + r * 110))

plt.figure(figsize=(8, 6))
plt.imshow(wall)
plt.axis("off")
plt.title("缩略图墙 2x3")
plt.savefig("collage-grid_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
wall.save("collage_demo.png")