"""散点图（平方增长）
数据可视化示例（matplotlib）。两变量相关性散点。
运行后在当前目录生成 'viz_scatter_d12'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(18)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 10, 60)
y = (np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60)
ax.scatter(x, y, s=18, c=y, cmap='viridis', alpha=0.85)
ax.set_title("散点图（平方增长）")
plt.tight_layout()
plt.savefig("'viz_scatter_d12'_preview.png", dpi=110)
print("已生成 'viz_scatter_d12'_preview.png")
