"""相关矩阵热力图：财务指标相关性"""
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


np.random.seed(21)
n = 200
revenue = np.random.normal(100, 20, n)
profit = revenue * 0.3 + np.random.normal(0, 5, n)
cost = revenue * 0.6 + np.random.normal(0, 8, n)
users = revenue * 0.8 + np.random.normal(0, 15, n)
satisfaction = -cost * 0.02 + np.random.normal(0, 0.5, n)
data = np.vstack([revenue, profit, cost, users, satisfaction])
corr = np.corrcoef(data)
labels = ["营收", "利润", "成本", "用户数", "满意度"]

plt.figure(figsize=(8, 7))
im = plt.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
plt.colorbar(im, label="相关系数")
plt.xticks(range(len(labels)), labels)
plt.yticks(range(len(labels)), labels)
for i in range(len(labels)):
    for j in range(len(labels)):
        plt.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                 color="white" if abs(corr[i, j]) > 0.6 else "black", fontsize=10)
plt.title("相关矩阵热力图：财务指标相关性")
plt.tight_layout()
plt.savefig("correlation-matrix_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")