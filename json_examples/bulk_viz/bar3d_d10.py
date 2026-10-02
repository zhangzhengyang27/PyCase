"""三维柱状（缓升陡降）
数据可视化示例（matplotlib）。3D 柱状矩阵。
运行后在当前目录生成 'viz_bar3d_d10'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(16)
fig, ax = plt.subplots(figsize=(8, 5))
ax.remove() if hasattr(ax, 'remove') else None
ax = fig.add_subplot(111, projection='3d')
data = np.abs(np.array(np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60)))
for i in range(6):
    for j in range(6):
        ax.bar3d(i, j, 0, 0.6, 0.6, data[(i * 6 + j) % len(data)] / 2, shade=True)
ax.set_title("三维柱状（缓升陡降）")
plt.tight_layout()
plt.savefig("'viz_bar3d_d10'_preview.png", dpi=110)
print("已生成 'viz_bar3d_d10'_preview.png")
