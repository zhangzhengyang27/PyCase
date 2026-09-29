"""分组柱状图：各部门季度销售额对比"""
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


quarters = ["Q1", "Q2", "Q3", "Q4"]
depts = ["技术部", "市场部", "销售部"]
sales = np.array([
    [120, 135, 148, 160],
    [80, 95, 110, 130],
    [200, 210, 230, 250],
])
x = np.arange(len(quarters))
width = 0.25
colors = ["#2e86de", "#e17055", "#00b894"]

plt.figure(figsize=(10, 6))
for i, (dept, color) in enumerate(zip(depts, colors)):
    plt.bar(x + (i - 1) * width, sales[i], width, label=dept, color=color)
for i in range(len(depts)):
    for j in range(len(quarters)):
        plt.text(x[j] + (i - 1) * width, sales[i][j] + 3, f"{sales[i][j]}",
                 ha="center", fontsize=9)
plt.xticks(x, quarters)
plt.xlabel("季度")
plt.ylabel("销售额（万元）")
plt.title("分组柱状图：各部门季度销售额对比")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("grouped-bar_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")