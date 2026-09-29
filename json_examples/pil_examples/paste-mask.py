"""蒙版粘贴合成：径向渐变无缝融合"""
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


W, H = 320, 320

# 底图：深蓝星空 + 随机亮点
bg = Image.new("RGB", (W, H), (8, 16, 48))
rng = np.random.default_rng(3)
d = ImageDraw.Draw(bg)
for _ in range(220):
    d.point((rng.integers(0, W), rng.integers(0, H)), fill=(255, 255, 255))

# 前景：暖色圆（模拟太阳/花朵）
fg = Image.new("RGB", (W, H), (255, 220, 60))
fd = ImageDraw.Draw(bg)
fd.ellipse([80, 80, 240, 240], fill=(255, 140, 40))

# 径向渐变蒙版：中心不透明 → 边缘透明
yy, xx = np.mgrid[0:H, 0:W]
dist = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / (W / 2)
mask = np.clip(1 - dist, 0, 1)
mask_img = Image.fromarray((mask * 255).astype(np.uint8), "L")

result = bg.copy()
result.paste(fg, (0, 0), mask_img)

plt.figure(figsize=(8, 8))
plt.imshow(result)
plt.axis("off")
plt.title("蒙版粘贴：径向渐变合成")
plt.savefig("paste-mask_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
result.save("paste_mask_demo.png")