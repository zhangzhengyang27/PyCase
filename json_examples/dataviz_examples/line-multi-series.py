"""多系列折线图：三只股票价格走势对比"""
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


np.random.seed(42)
days = np.arange(1, 61)  # 60 个交易日
base = 100
stock_a = base + np.cumsum(np.random.normal(0.5, 2, len(days)))
stock_b = base + np.cumsum(np.random.normal(0.2, 3, len(days)))
stock_c = base + np.cumsum(np.random.normal(-0.1, 1.5, len(days)))

plt.figure(figsize=(10, 6))
plt.plot(days, stock_a, label="股票 A", linewidth=2, color="#2e86de")
plt.plot(days, stock_b, label="股票 B", linewidth=2, color="#e17055")
plt.plot(days, stock_c, label="股票 C", linewidth=2, color="#00b894")
plt.xlabel("交易日")
plt.ylabel("价格")
plt.title("多系列折线图：三只股票的价格走势")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("line-multi-series_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")