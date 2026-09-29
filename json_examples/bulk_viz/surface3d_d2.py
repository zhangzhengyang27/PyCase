"""三维曲面（线性趋势）
数据可视化示例（matplotlib）。3D 高斯曲面。
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
x = np.linspace(-3, 3, 60); yv = np.linspace(-3, 3, 60)
X, Y = np.meshgrid(x, yv)
Z = np.exp(-(X ** 2 + Y ** 2) / 2) * np.cos(2 * X)
ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9)
ax.set_title("三维曲面（线性趋势）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
