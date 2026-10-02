"""双轴对比（平方增长）
数据可视化示例（matplotlib）。折线 + 柱状双 y 轴对比。
运行后在当前目录生成 'viz_dual-axis_d12'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(18)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array((np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60))
ax2 = ax.twinx()
ax.bar(np.arange(len(data))[::6], data[::6].mean() + data[::6].std(), alpha=0.3, color='tab:gray')
ax2.plot(data, color='crimson', linewidth=1.4)
ax.set_ylabel('柱'); ax2.set_ylabel('线')
ax.set_title("双轴对比（平方增长）")
plt.tight_layout()
plt.savefig("'viz_dual-axis_d12'_preview.png", dpi=110)
print("已生成 'viz_dual-axis_d12'_preview.png")
