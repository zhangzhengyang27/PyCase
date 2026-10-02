"""热力图（阶梯平台）
数据可视化示例（matplotlib）。矩阵热力图（imshow + 色标）。
运行后在当前目录生成 'viz_heatmap_d7'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(13)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.repeat(rng.uniform(1, 9, 10), 6) + rng.normal(0, 0.2, 60))
mat = np.outer(data, data)[:20, :]
im = ax.imshow(mat, aspect='auto', cmap='magma')
fig.colorbar(im, ax=ax)
ax.set_title("热力图（阶梯平台）")
plt.tight_layout()
plt.savefig("'viz_heatmap_d7'_preview.png", dpi=110)
print("已生成 'viz_heatmap_d7'_preview.png")
