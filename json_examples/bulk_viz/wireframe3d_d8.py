"""三维线框（双峰分布）
数据可视化示例（matplotlib）。3D 线框波纹。
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
x = np.linspace(-3, 3, 40); yv = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, yv)
ax.plot_wireframe(X, Y, np.sin(X) * np.cos(Y), rstride=2, cstride=2, color='tab:teal')
ax.set_title("三维线框（双峰分布）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
