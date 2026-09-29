"""气泡图：GDP、人口与增长率"""
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


np.random.seed(1)
n = 30
gdp = np.random.uniform(10, 100, n)        # GDP（千亿美元）
population = np.random.uniform(1, 14, n)   # 人口（亿）
growth = np.random.uniform(-2, 8, n)       # 增长率（%）

plt.figure(figsize=(10, 7))
sc = plt.scatter(gdp, population, s=growth * 60 + 30, c=growth, cmap="RdYlGn",
                 alpha=0.7, edgecolors="w")
plt.colorbar(sc, label="增长率（%）")
plt.xlabel("GDP（千亿美元）")
plt.ylabel("人口（亿）")
plt.title("气泡图：GDP、人口与增长率")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("bubble-chart_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")