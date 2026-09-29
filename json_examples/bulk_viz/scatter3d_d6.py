"""三维散点（周期脉冲）
数据可视化示例（matplotlib）。3D 螺旋散点。
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
t = np.linspace(0, 8 * np.pi, 300)
ax.scatter(np.cos(t) * t * 0.12, np.sin(t) * t * 0.12, t, c=t, cmap='plasma', s=8)
ax.set_title("三维散点（周期脉冲）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
