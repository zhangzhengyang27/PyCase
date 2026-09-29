"""水平条形图：商品销量排行榜"""
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


products = ["无线耳机", "智能手表", "蓝牙音箱", "移动电源", "机械键盘", "游戏鼠标"]
sales = [320, 280, 235, 210, 185, 150]
order = np.argsort(sales)
products = [products[i] for i in order]
sales = sorted(sales)
colors = ["#feca57"] + ["#74b9ff"] * (len(sales) - 1)

plt.figure(figsize=(10, 6))
bars = plt.barh(products, sales, color=colors)
plt.xlabel("销量（件）")
plt.title("水平条形图：商品销量排行榜")
for bar in bars:
    plt.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
             f"{bar.get_width():.0f}", va="center", fontsize=10)
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("horizontal-bar-rank_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")