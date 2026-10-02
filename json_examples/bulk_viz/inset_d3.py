"""局部放大（指数衰减）
数据可视化示例（matplotlib）。主图 + 局部放大插图。
运行后在当前目录生成 'viz_inset_d3'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(9)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(8 * np.exp(-np.linspace(0, 4, 60)) + rng.normal(0, 0.12, 60))
ax.plot(data, linewidth=1.2)
axi = ax.inset_axes([0.55, 0.55, 0.4, 0.38])
seg = data[20:32]
axi.plot(seg, color='tomato'); axi.tick_params(labelsize=6)
ax.indicate_inset_zoom(axi)
ax.set_title("局部放大（指数衰减）")
plt.tight_layout()
plt.savefig("'viz_inset_d3'_preview.png", dpi=110)
print("已生成 'viz_inset_d3'_preview.png")
