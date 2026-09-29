"""矢量场（正弦加噪）
数据可视化示例（matplotlib）。旋转矢量场箭头图。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(-2, 2, 10); yv = np.linspace(-2, 2, 10)
X, Y = np.meshgrid(x, yv)
U, Vv = -Y, X
ax.quiver(X, Y, U, Vv, color='tab:blue')
ax.set_title("矢量场（正弦加噪）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
