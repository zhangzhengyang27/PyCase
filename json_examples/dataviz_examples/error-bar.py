"""误差棒图：各方案转化率对比"""
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


groups = ["对照组", "方案 A", "方案 B", "方案 C"]
means = [42, 55, 63, 58]
stds = [4, 6, 5, 7]

plt.figure(figsize=(9, 6))
plt.errorbar(range(len(groups)), means, yerr=stds, fmt="o", capsize=6,
             color="#2e86de", ecolor="#e17055", elinewidth=2, markersize=8)
plt.xticks(range(len(groups)), groups)
plt.ylabel("转化率（%）")
plt.title("误差棒图：各方案转化率对比")
plt.grid(axis="y", alpha=0.3)
for i, (m, s) in enumerate(zip(means, stds)):
    plt.text(i, m + s + 1.5, f"{m}±{s}", ha="center", fontsize=9)
plt.ylim(0, 80)
plt.tight_layout()
plt.savefig("error-bar_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")