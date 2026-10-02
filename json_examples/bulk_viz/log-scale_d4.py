"""对数坐标（均匀随机）
数据可视化示例（matplotlib）。指数增长对数轴。
运行后在当前目录生成 'viz_log-scale_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(1, 61)
y = np.exp(0.07 * x) * (1 + np.array(rng.uniform(0, 10, 60)) / 20)
ax.semilogy(x, y, color='tab:gray')
ax.grid(alpha=0.3, which='both')
ax.set_title("对数坐标（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_log-scale_d4'_preview.png", dpi=110)
print("已生成 'viz_log-scale_d4'_preview.png")
