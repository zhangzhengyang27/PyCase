"""置信区间填充图：均值趋势与置信带"""
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


np.random.seed(7)
x = np.linspace(0, 10, 50)
true_y = np.sin(x) * 5 + 10
trials = 30
ys = np.array([true_y + np.random.normal(0, 1.2, len(x)) for _ in range(trials)])
mean = ys.mean(axis=0)
std = ys.std(axis=0)

plt.figure(figsize=(10, 6))
plt.plot(x, mean, label="均值", color="#0984e3", linewidth=2)
plt.fill_between(x, mean - std, mean + std, alpha=0.25, color="#0984e3", label="±1σ")
plt.fill_between(x, mean - 2 * std, mean + 2 * std, alpha=0.12, color="#0984e3", label="±2σ")
plt.scatter(x, ys[0], s=12, alpha=0.5, color="#b2bec3", label="单次试验")
plt.xlabel("x")
plt.ylabel("y")
plt.title("置信区间填充图：均值与标准差")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("line-confidence-band_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")