"""3D 散点图：样本空间分布"""
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


np.random.seed(15)
n = 120
x = np.random.normal(0, 1, n)
y = np.random.normal(0, 1, n)
z = x ** 2 + y ** 2 + np.random.normal(0, 0.3, n)

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")
sc = ax.scatter(x, y, z, c=z, cmap="plasma", s=30, alpha=0.8)
fig.colorbar(sc, ax=ax, shrink=0.6, label="z 值")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D 散点图：样本空间分布")
plt.tight_layout()
plt.savefig("scatter-3d_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")