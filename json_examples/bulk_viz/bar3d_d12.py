"""三维柱状（平方增长）
数据可视化示例（matplotlib）。3D 柱状矩阵。
运行后在当前目录生成 'viz_bar3d_d12'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(18)
fig, ax = plt.subplots(figsize=(8, 5))
ax.remove() if hasattr(ax, 'remove') else None
ax = fig.add_subplot(111, projection='3d')
data = np.abs(np.array((np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60)))
for i in range(6):
    for j in range(6):
        ax.bar3d(i, j, 0, 0.6, 0.6, data[(i * 6 + j) % len(data)] / 2, shade=True)
ax.set_title("三维柱状（平方增长）")
plt.tight_layout()
plt.savefig("'viz_bar3d_d12'_preview.png", dpi=110)
print("已生成 'viz_bar3d_d12'_preview.png")
