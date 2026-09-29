"""等高线（阶梯平台）
数据可视化示例（matplotlib）。二维高斯等高线。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(-3, 3, 80); yv = np.linspace(-2, 2, 60)
X, Y = np.meshgrid(x, yv)
Z = np.exp(-(X ** 2 + Y ** 2)) + 0.4 * np.sin(2 * X) * np.cos(Y)
cs = ax.contourf(X, Y, Z, levels=14, cmap='coolwarm')
fig.colorbar(cs, ax=ax)
ax.set_title("等高线（阶梯平台）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
