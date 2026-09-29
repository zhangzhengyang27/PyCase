"""缩放与缩略图：不同重采样算法对比"""
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


# 程序化生成 320x320 棋盘格
W = 320
img = Image.new("RGB", (W, W), "white")
d = ImageDraw.Draw(img)
for i in range(8):
    for j in range(8):
        if (i + j) % 2 == 0:
            d.rectangle([i * 40, j * 40, i * 40 + 40, j * 40 + 40], fill=(30, 144, 255))

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(img)
axes[0, 0].set_title("原图 320x320")
axes[0, 0].axis("off")

modes = [("最近邻", Image.Resampling.NEAREST), ("双线性", Image.Resampling.BILINEAR),
         ("双三次", Image.Resampling.BICUBIC)]
for ax, (label, mode) in zip(axes.flat[1:], modes):
    small = img.resize((100, 100), mode).resize((320, 320), mode)
    ax.imshow(small)
    ax.set_title(label)
    ax.axis("off")

plt.suptitle("缩放算法对比：先缩到 1/3 再放大回原尺寸")
plt.tight_layout()
plt.savefig("resize-thumbnail_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")

thumb = img.copy()
thumb.thumbnail((96, 96))
print("缩略图尺寸:", thumb.size)
thumb.save("thumbnail_demo.png")