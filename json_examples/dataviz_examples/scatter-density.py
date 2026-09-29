"""散点密度图：2000 个样本的分布"""
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


np.random.seed(3)
n = 2000
x = np.random.normal(0, 1, n)
y = x * 0.8 + np.random.normal(0, 0.5, n)

plt.figure(figsize=(10, 7))
plt.scatter(x, y, s=8, c="#0984e3", alpha=0.15, edgecolors="none")
plt.xlabel("x")
plt.ylabel("y")
plt.title("散点密度图：2000 个样本的分布")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("scatter-density_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")