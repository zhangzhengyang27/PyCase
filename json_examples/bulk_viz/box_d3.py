"""箱线图（指数衰减）
数据可视化示例（matplotlib）。分箱箱线图（四分位与离群）。
运行后在当前目录生成 'viz_box_d3'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(9)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(8 * np.exp(-np.linspace(0, 4, 60)) + rng.normal(0, 0.12, 60))
bins = [data[i:i+10] for i in range(0, 60, 10)]
ax.boxplot(bins, patch_artist=True, boxprops=dict(facecolor='lightyellow'))
ax.set_title("箱线图（指数衰减）")
plt.tight_layout()
plt.savefig("'viz_box_d3'_preview.png", dpi=110)
print("已生成 'viz_box_d3'_preview.png")
