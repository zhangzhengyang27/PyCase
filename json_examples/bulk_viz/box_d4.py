"""箱线图（均匀随机）
数据可视化示例（matplotlib）。分箱箱线图（四分位与离群）。
运行后在当前目录生成 'viz_box_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(rng.uniform(0, 10, 60))
bins = [data[i:i+10] for i in range(0, 60, 10)]
ax.boxplot(bins, patch_artist=True, boxprops=dict(facecolor='lightyellow'))
ax.set_title("箱线图（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_box_d4'_preview.png", dpi=110)
print("已生成 'viz_box_d4'_preview.png")
