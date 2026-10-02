"""直方图（缓升陡降）
数据可视化示例（matplotlib）。分布直方图与密度核。
运行后在当前目录生成 'viz_hist_d10'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(16)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60))
ax.hist(data, bins=16, color='tab:green', edgecolor='white')
ax.set_title("直方图（缓升陡降）")
plt.tight_layout()
plt.savefig("'viz_hist_d10'_preview.png", dpi=110)
print("已生成 'viz_hist_d10'_preview.png")
