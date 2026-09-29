"""复古滤镜：棕褐调 + 暗角 + 噪点"""
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


# 程序化生成"照片"素材
W, H = 360, 260
img = Image.new("RGB", (W, H), (140, 190, 140))
d = ImageDraw.Draw(img)
d.rectangle([0, 160, W, H], fill=(90, 140, 90))          # 草地
d.rectangle([140, 120, 220, 180], fill=(200, 150, 120))  # 小房子
d.polygon([(120, 120), (180, 70), (240, 120)], fill=(150, 90, 70))  # 屋顶
d.ellipse([60, 40, 130, 90], fill=(255, 220, 90))        # 太阳

arr = np.asarray(img).astype(np.float32)

# 1) 棕褐色调
gray = arr.mean(axis=2, keepdims=True)
arr = arr * 0.55 + gray * 0.45
arr[..., 0] = np.clip(arr[..., 0] * 1.12, 0, 255)   # R 偏暖
arr[..., 2] = np.clip(arr[..., 2] * 0.88, 0, 255)   # B 偏冷

# 2) 暗角
yy, xx = np.mgrid[0:H, 0:W]
dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
vignette = np.clip(1 - dist * 0.55, 0, 1)[..., None]
arr = arr * vignette

# 3) 胶片噪点
rng = np.random.default_rng(11)
arr = arr + rng.normal(0, 6, arr.shape)

out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(img)
axes[0].set_title("原图")
axes[0].axis("off")
axes[1].imshow(out)
axes[1].set_title("复古滤镜效果")
axes[1].axis("off")
plt.tight_layout()
plt.savefig("vintage-filter_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")