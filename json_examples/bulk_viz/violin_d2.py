"""小提琴图（线性趋势）
数据可视化示例（matplotlib）。分箱小提琴分布。
运行后在当前目录生成 'viz_violin_d2'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(8)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.linspace(2, 9, 60) + rng.normal(0, 0.4, 60))
bins = [data[i:i+10] for i in range(0, 60, 10)]
parts = ax.violinplot(bins, showmedians=True)
for pc in parts['bodies']: pc.set_facecolor('tab:purple'); pc.set_alpha(0.6)
ax.set_title("小提琴图（线性趋势）")
plt.tight_layout()
plt.savefig("'viz_violin_d2'_preview.png", dpi=110)
print("已生成 'viz_violin_d2'_preview.png")
