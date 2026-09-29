"""直方图与密度曲线：学生成绩分布"""
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


np.random.seed(11)
scores = np.concatenate([np.random.normal(72, 12, 400), np.random.normal(55, 8, 100)])

plt.figure(figsize=(10, 6))
counts, bins, patches = plt.hist(scores, bins=30, density=True, alpha=0.6,
                                 color="#2e86de", label="直方图")
# 用滑动平均平滑出密度曲线（避免依赖 scipy）
centers = (bins[:-1] + bins[1:]) / 2
smooth = np.convolve(counts, np.ones(5) / 5, mode="same")
plt.plot(centers, smooth, color="#e17055", linewidth=2.5, label="密度曲线")
plt.xlabel("成绩")
plt.ylabel("密度")
plt.title("直方图与密度曲线：学生成绩分布")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("histogram-kde_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")