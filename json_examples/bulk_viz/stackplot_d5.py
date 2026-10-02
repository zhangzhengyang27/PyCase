"""堆叠面积图（聚簇正态）
数据可视化示例（matplotlib）。三分量堆叠时序。
运行后在当前目录生成 'viz_stackplot_d5'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(11)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(60)
data = np.array(np.concatenate([rng.normal(3, 0.5, 30), rng.normal(7, 0.5, 30)]))
a = np.abs(data) / data.max() * 4
ax.stackplot(x, a, a * 0.6 + 1, a * 0.3 + 2, labels=['A', 'B', 'C'], alpha=0.8)
ax.legend(loc='upper left')
ax.set_title("堆叠面积图（聚簇正态）")
plt.tight_layout()
plt.savefig("'viz_stackplot_d5'_preview.png", dpi=110)
print("已生成 'viz_stackplot_d5'_preview.png")
