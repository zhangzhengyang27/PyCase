"""误差条图（周期脉冲）
数据可视化示例（matplotlib）。均值 ± 标准差误差条。
运行后在当前目录生成 'viz_errorbar_d6'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(12)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60)))
bins = [data[i:i+10] for i in range(0, 60, 10)]
means = [b.mean() for b in bins]
stds = [b.std() for b in bins]
ax.errorbar(range(len(bins)), means, yerr=stds, fmt='o', capsize=4, color='tab:brown')
ax.set_title("误差条图（周期脉冲）")
plt.tight_layout()
plt.savefig("'viz_errorbar_d6'_preview.png", dpi=110)
print("已生成 'viz_errorbar_d6'_preview.png")
