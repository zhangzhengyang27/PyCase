"""三维柱状（阶梯平台）
数据可视化示例（matplotlib）。3D 柱状矩阵。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
ax.remove() if hasattr(ax, 'remove') else None
ax = fig.add_subplot(111, projection='3d')
data = np.abs(np.array(y = np.repeat(rng.uniform(1, 9, 10), 6) + rng.normal(0, 0.2, 60)))
for i in range(6):
    for j in range(6):
        ax.bar3d(i, j, 0, 0.6, 0.6, data[(i * 6 + j) % len(data)] / 2, shade=True)
ax.set_title("三维柱状（阶梯平台）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
