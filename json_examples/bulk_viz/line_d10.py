"""折线图（缓升陡降）
数据可视化示例（matplotlib）。单序列折线与标记点。
运行后在当前目录生成 'viz_line_d10'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(16)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60)))
y = np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60)
ax.plot(x, y, marker='o', markersize=3, linewidth=1.6, color='tab:blue')
ax.grid(alpha=0.3)
ax.set_title("折线图（缓升陡降）")
plt.tight_layout()
plt.savefig("'viz_line_d10'_preview.png", dpi=110)
print("已生成 'viz_line_d10'_preview.png")
