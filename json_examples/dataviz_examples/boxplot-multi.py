"""箱线图：四个班级成绩分布对比"""
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


np.random.seed(5)
data = [
    np.random.normal(75, 8, 50),
    np.random.normal(70, 12, 50),
    np.random.normal(82, 6, 50),
    np.random.normal(65, 15, 50),
]
labels = ["一班", "二班", "三班", "四班"]

plt.figure(figsize=(9, 6))
bp = plt.boxplot(data, patch_artist=True, widths=0.5)
plt.xticks(range(1, len(labels) + 1), labels)
colors = ["#74b9ff", "#a29bfe", "#55efc4", "#fab1a0"]
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
plt.ylabel("成绩")
plt.title("箱线图：四个班级成绩分布对比")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("boxplot-multi_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")