"""样式表对比：同一数据不同风格"""
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


styles = ["default", "ggplot", "dark_background", "fivethirtyeight"]
x = np.linspace(0, 2 * np.pi, 60)

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, style in zip(axes.flat, styles):
    with plt.style.context(style):
        ax.plot(x, np.sin(x), label="sin(x)", linewidth=2)
        ax.plot(x, np.cos(x), label="cos(x)", linewidth=2)
        ax.fill_between(x, np.sin(x), np.cos(x), alpha=0.15)
    ax.set_title(f"Style: {style}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
plt.suptitle("样式表对比：同一数据不同风格")
plt.tight_layout()
plt.savefig("style-compare_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")