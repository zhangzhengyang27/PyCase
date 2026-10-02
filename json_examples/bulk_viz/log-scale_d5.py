"""对数坐标（聚簇正态）
数据可视化示例（matplotlib）。指数增长对数轴。
运行后在当前目录生成 'viz_log-scale_d5'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(11)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(1, 61)
y = np.exp(0.07 * x) * (1 + np.array(np.concatenate([rng.normal(3, 0.5, 30), rng.normal(7, 0.5, 30)])) / 20)
ax.semilogy(x, y, color='tab:gray')
ax.grid(alpha=0.3, which='both')
ax.set_title("对数坐标（聚簇正态）")
plt.tight_layout()
plt.savefig("'viz_log-scale_d5'_preview.png", dpi=110)
print("已生成 'viz_log-scale_d5'_preview.png")
