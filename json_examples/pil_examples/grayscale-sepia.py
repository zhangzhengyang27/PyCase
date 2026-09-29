"""灰度化与老照片：彩色图 → 灰度 → 棕褐色调"""
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


# 程序化生成"风景"：天空渐变 + 绿色山丘 + 橙色太阳
W, H = 400, 300
sky = np.linspace(135, 206, H, dtype=np.uint8).reshape(-1, 1)
arr = np.zeros((H, W, 3), dtype=np.uint8)
arr[:, :, 0] = np.tile(sky, (1, W))
arr[:, :, 1] = 180
arr[:, :, 2] = 235
arr[H // 2:, :, 0] = 60
arr[H // 2:, :, 1] = 160
arr[H // 2:, :, 2] = 80
sun = Image.fromarray(arr, "RGB")
d = ImageDraw.Draw(sun)
d.ellipse([150, 80, 250, 180], fill=(255, 160, 40))

gray = sun.convert("L")

# 棕褐色：L -> (R,G,B) = (L*1.05, L*0.87, L*0.58)
g = np.asarray(gray).astype(np.float32)
sepia = np.stack([g * 1.05, g * 0.87, g * 0.58], axis=-1)
sepia = np.clip(sepia, 0, 255).astype(np.uint8)
sepia = Image.fromarray(sepia)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, im, t in zip(axes, [sun, gray, sepia], ["原图", "灰度", "老照片棕褐"]):
    ax.imshow(im, cmap="gray" if im.mode == "L" else None)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.savefig("grayscale-sepia_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")