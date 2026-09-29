"""实时动画折线图：滑动窗口数据流"""
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

from matplotlib.animation import FuncAnimation

np.random.seed(9)
fig, ax = plt.subplots(figsize=(10, 6))
x_data, y_data = [], []
line, = ax.plot([], [], color="#2e86de", linewidth=2)
ax.set_xlim(0, 50)
ax.set_ylim(-3, 3)
ax.grid(alpha=0.3)
ax.set_title("实时动画折线图：正弦波 + 噪声")


def update(frame):
    x_data.append(frame)
    y_data.append(np.sin(frame * 0.3) + np.random.normal(0, 0.15))
    if len(x_data) > 50:
        x_data.pop(0)
        y_data.pop(0)
    line.set_data(x_data, y_data)
    return line,


ani = FuncAnimation(fig, update, frames=range(80), interval=150, blit=True)
plt.savefig("animated-line_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")