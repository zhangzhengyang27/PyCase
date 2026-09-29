"""渐变图像生成器：程序化创建 RGB 渐变图"""
from PIL import Image
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


W, H = 400, 300

# 水平渐变：R 从左到右 0->255
x = np.linspace(0, 255, W, dtype=np.uint8)
horiz = np.tile(x, (H, 1))

# 垂直渐变：G 从上到下 0->255
y = np.linspace(0, 255, H, dtype=np.uint8).reshape(-1, 1)
vert = np.tile(y, (1, W))

# 对角渐变：B 从 (0,0) 到 (W,H)
diag = np.linspace(0, 255, W + H, dtype=np.uint8)
diag_map = np.array([[diag[i + j] for j in range(W)] for i in range(H)])

rgb = np.stack([horiz, vert, diag_map], axis=-1).astype(np.uint8)
img = Image.fromarray(rgb, "RGB")

plt.figure(figsize=(8, 6))
plt.imshow(img)
plt.axis("off")
plt.title("RGB 渐变图：R 水平 / G 垂直 / B 对角")
plt.savefig("gradient-generator_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")
img.save("gradient_demo.png")
print("已保存 gradient_demo.png")