"""网格密底图（均匀随机）
数据可视化示例（matplotlib）。密网格 + 参考线风格化折线。
运行后在当前目录生成 'viz_style-grid_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(rng.uniform(0, 10, 60))
ax.plot(data, color='#2c3e50', linewidth=2)
ax.axhline(data.mean(), ls='--', color='tomato', label='均值')
ax.legend(); ax.minorticks_on(); ax.grid(alpha=0.25)
ax.set_title("网格密底图（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_style-grid_d4'_preview.png", dpi=110)
print("已生成 'viz_style-grid_d4'_preview.png")
