"""堆叠柱状图：网站流量来源构成"""
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


months = ["1月", "2月", "3月", "4月", "5月", "6月"]
direct = [30, 35, 40, 38, 45, 52]
search = [55, 60, 58, 62, 66, 70]
social = [15, 18, 20, 24, 26, 30]

plt.figure(figsize=(10, 6))
plt.bar(months, direct, label="直接访问", color="#2e86de")
plt.bar(months, search, bottom=direct, label="搜索引擎", color="#e17055")
plt.bar(months, social, bottom=np.array(direct) + np.array(search),
        label="社交媒体", color="#00b894")
plt.xlabel("月份")
plt.ylabel("访问量（千次）")
plt.title("堆叠柱状图：网站流量来源构成")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("stacked-bar_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")