"""网格密底图（聚簇正态）
数据可视化示例（matplotlib）。密网格 + 参考线风格化折线。
运行后在当前目录生成 'viz_style-grid_d5'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(11)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.concatenate([rng.normal(3, 0.5, 30), rng.normal(7, 0.5, 30)]))
ax.plot(data, color='#2c3e50', linewidth=2)
ax.axhline(data.mean(), ls='--', color='tomato', label='均值')
ax.legend(); ax.minorticks_on(); ax.grid(alpha=0.25)
ax.set_title("网格密底图（聚簇正态）")
plt.tight_layout()
plt.savefig("'viz_style-grid_d5'_preview.png", dpi=110)
print("已生成 'viz_style-grid_d5'_preview.png")
