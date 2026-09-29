from PIL import Image, ImageDraw
"""边缘检测流水线：降噪 → 找边缘 → 增强"""
from PIL import Image, ImageFilter, ImageOps
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


# 程序化生成带噪点的几何图
W, H = 300, 300
img = Image.new("RGB", (W, H), (245, 245, 245))
d = ImageDraw.Draw(img)
d.rectangle([40, 40, 260, 260], outline=(40, 40, 40), width=4)
d.ellipse([90, 90, 210, 210], outline=(40, 40, 40), width=4)
d.line([(40, 260), (260, 40)], fill=(40, 40, 40), width=4)

# 加椒盐噪点
arr = np.asarray(img).copy()
rng = np.random.default_rng(7)
mask = rng.random((H, W)) < 0.03
arr[mask] = [0, 0, 0]
noisy = Image.fromarray(arr)

# 流水线
denoised = noisy.filter(ImageFilter.GaussianBlur(1.2))
edges = denoised.filter(ImageFilter.FIND_EDGES).convert("L")
edges_enhanced = ImageOps.autocontrast(edges)

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
for ax, im, t in zip(axes.flat,
                     [noisy, denoised, edges, edges_enhanced],
                     ["带噪原图", "高斯降噪", "查找边缘", "自动对比度增强"]):
    ax.imshow(im, cmap="gray" if im.mode == "L" else None)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.savefig("edge-detect_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")