"""裁剪与粘贴合成：拼贴画效果"""
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


# 生成 300x300 渐变底图
import numpy as np
xx = np.linspace(0, 255, 300, dtype=np.uint8)
base = Image.fromarray(np.tile(xx, (300, 1)).astype(np.uint8), "L").convert("RGB")

# 生成黄色圆
yellow = Image.new("RGB", (150, 150), "white")
d = ImageDraw.Draw(yellow)
d.ellipse([10, 10, 140, 140], fill=(255, 215, 0))
# 生成青色方块
cyan = Image.new("RGB", (150, 150), "white")
d2 = ImageDraw.Draw(cyan)
d2.rectangle([30, 30, 120, 120], fill=(0, 200, 200))

# 裁剪渐变图左上 150x150
crop = base.crop((0, 0, 150, 150))

# 拼贴：底图 + 四角元素
canvas = Image.new("RGB", (450, 450), "lightgray")
canvas.paste(base, (0, 0))
canvas.paste(yellow, (150, 0))
canvas.paste(cyan, (300, 0))
canvas.paste(crop.rotate(180), (0, 150))
canvas.paste(crop.rotate(90), (150, 150))
canvas.paste(crop.rotate(270), (300, 150))

plt.figure(figsize=(8, 8))
plt.imshow(canvas)
plt.axis("off")
plt.title("裁剪与粘贴合成拼贴画")
plt.savefig("crop-paste_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
canvas.save("crop_paste_demo.png")