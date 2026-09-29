"""对数坐标图：线性坐标 vs 对数坐标"""
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


x = np.logspace(0, 5, 100)
y1 = x ** 2
y2 = x ** 1.5

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.plot(x, y1, label="y = x²")
ax1.plot(x, y2, label="y = x^1.5")
ax1.set_title("线性坐标")
ax1.set_xlabel("x")
ax1.set_ylabel("y")
ax1.legend()
ax1.grid(alpha=0.3)

ax2.plot(x, y1, label="y = x²")
ax2.plot(x, y2, label="y = x^1.5")
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_title("对数坐标")
ax2.set_xlabel("x（对数）")
ax2.set_ylabel("y（对数）")
ax2.legend()
ax2.grid(alpha=0.3, which="both")
plt.tight_layout()
plt.savefig("log-scale_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")