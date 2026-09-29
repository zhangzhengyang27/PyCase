"""带注释热力图：各城市月均气温"""
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


cities = ["北京", "上海", "广州", "成都", "哈尔滨"]
months = ["1月", "3月", "5月", "7月", "9月", "11月"]
temp = np.array([
    [-3, 6, 20, 27, 20, 5],
    [5, 10, 21, 29, 24, 12],
    [14, 18, 26, 29, 27, 20],
    [6, 12, 21, 25, 21, 12],
    [-19, -5, 12, 23, 12, -8],
])

plt.figure(figsize=(9, 6))
im = plt.imshow(temp, cmap="coolwarm", aspect="auto")
plt.colorbar(im, label="平均气温（°C）")
plt.xticks(range(len(months)), months)
plt.yticks(range(len(cities)), cities)
for i in range(len(cities)):
    for j in range(len(months)):
        plt.text(j, i, f"{temp[i, j]:.0f}", ha="center", va="center",
                 color="white" if abs(temp[i, j]) > 15 else "black", fontsize=11)
plt.title("热力图：各城市月均气温")
plt.tight_layout()
plt.savefig("heatmap-annotated_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")