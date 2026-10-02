"""双子图布局（缓升陡降）
数据可视化示例（matplotlib）。1×2 子图：折线 + 直方。
运行后在当前目录生成 'viz_twin-styles_d10'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(16)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60))
ax.remove() if hasattr(ax, 'remove') else None
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.5))
a1.plot(data, color='tab:blue'); a1.set_title('折线')
a2.hist(data, bins=14, color='tab:orange'); a2.set_title('分布')
ax.set_title("双子图布局（缓升陡降）")
plt.tight_layout()
plt.savefig("'viz_twin-styles_d10'_preview.png", dpi=110)
print("已生成 'viz_twin-styles_d10'_preview.png")
