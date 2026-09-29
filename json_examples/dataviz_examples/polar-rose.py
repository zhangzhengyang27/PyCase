"""极坐标玫瑰图：风向频数分布"""
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


np.random.seed(8)
dirs = np.array([0, 45, 90, 135, 180, 225, 270, 315])
directions = np.random.choice(dirs, size=500)

theta = np.radians(dirs)
counts = [int(np.sum(directions == d)) for d in dirs]

plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)
bars = ax.bar(theta, counts, width=np.radians(45), color="#2e86de",
              alpha=0.75, edgecolor="white")
labels = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
ax.set_xticks(theta)
ax.set_xticklabels(labels)
ax.set_title("极坐标玫瑰图：风向频数分布")
plt.tight_layout()
plt.savefig("polar-rose_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")