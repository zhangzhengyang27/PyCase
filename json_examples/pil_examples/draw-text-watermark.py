from PIL import Image, ImageDraw
"""文字与水印：标题文字 + 半透明水印"""
from PIL import Image, ImageDraw, ImageFont
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


# 生成渐变底图
import numpy as np
xx = np.linspace(180, 120, 360, dtype=np.uint8)
img = Image.fromarray(np.tile(xx, (240, 1)), "L").convert("RGB")
d = ImageDraw.Draw(img)

# 尝试加载系统中文字体（找不到则用默认字体）
font_paths = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc",
              "/System/Library/Fonts/Supplemental/Songti.ttc", "C:/Windows/Fonts/msyh.ttc"]
font = None
for fp in font_paths:
    try:
        font = ImageFont.truetype(fp, 28)
        break
    except Exception:
        continue
if font is None:
    font = ImageFont.load_default()

d.text((24, 90), "示例管理器 DEMO", font=font, fill=(255, 255, 255))

# 半透明水印（平铺）
wm = Image.new("RGBA", img.size, (0, 0, 0, 0))
wd = ImageDraw.Draw(wm)
for x in range(0, 360, 130):
    for y in range(0, 240, 80):
        wd.text((x, y), "WATERMARK", font=font, fill=(255, 255, 255, 60))
img = Image.alpha_composite(img.convert("RGBA"), wm)

plt.figure(figsize=(9, 6))
plt.imshow(img)
plt.axis("off")
plt.title("文字与水印效果")
plt.savefig("draw-text-watermark_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
img.save("watermark_demo.png")