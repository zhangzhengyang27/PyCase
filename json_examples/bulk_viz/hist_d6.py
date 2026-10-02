"""直方图（周期脉冲）
数据可视化示例（matplotlib）。分布直方图与密度核。
运行后在当前目录生成 'viz_hist_d6'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(12)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60)))
ax.hist(data, bins=16, color='tab:green', edgecolor='white')
ax.set_title("直方图（周期脉冲）")
plt.tight_layout()
plt.savefig("'viz_hist_d6'_preview.png", dpi=110)
print("已生成 'viz_hist_d6'_preview.png")
