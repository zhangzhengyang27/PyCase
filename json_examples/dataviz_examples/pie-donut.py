"""饼图与环形图：产品线收入占比"""
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


labels = ["手机", "电脑", "平板", "穿戴设备", "配件"]
sizes = [35, 28, 15, 12, 10]
colors = ["#2e86de", "#e17055", "#00b894", "#fdcb6e", "#a29bfe"]
explode = (0.05, 0, 0, 0, 0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))
ax1.pie(sizes, labels=labels, colors=colors, explode=explode,
        autopct="%1.1f%%", startangle=90)
ax1.set_title("饼图：产品线收入占比")
ax2.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90,
        wedgeprops=dict(width=0.4, edgecolor="w"))
ax2.set_title("环形图：产品线收入占比")
plt.tight_layout()
plt.savefig("pie-donut_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")