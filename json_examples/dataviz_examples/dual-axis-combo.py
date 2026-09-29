"""双轴组合图：月度销售额与同比增长率"""
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


months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月"]
sales = [120, 135, 128, 150, 168, 175, 190, 210]
growth = [8, 12, -5, 17, 12, 4, 8, 10]

fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.bar(months, sales, color="#74b9ff", alpha=0.8, label="销售额（万元）")
ax1.set_ylabel("销售额（万元）", color="#2e86de")
ax1.set_ylim(0, 250)
ax1.tick_params(axis="y", labelcolor="#2e86de")

ax2 = ax1.twinx()
ax2.plot(months, growth, "o-", color="#e17055", linewidth=2, label="同比增长率（%）")
ax2.set_ylabel("同比增长率（%）", color="#e17055")
ax2.set_ylim(-20, 30)
ax2.tick_params(axis="y", labelcolor="#e17055")
ax2.axhline(0, color="gray", linewidth=0.8, linestyle="--")

plt.title("双轴组合图：月度销售额与同比增长率")
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.tight_layout()
plt.savefig("dual-axis-combo_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")