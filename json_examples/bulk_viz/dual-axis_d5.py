"""双轴对比（聚簇正态）
数据可视化示例（matplotlib）。折线 + 柱状双 y 轴对比。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = np.concatenate([rng.normal(3, 0.5, 30), rng.normal(7, 0.5, 30)]))
ax2 = ax.twinx()
ax.bar(np.arange(len(data))[::6], data[::6].mean() + data[::6].std(), alpha=0.3, color='tab:gray')
ax2.plot(data, color='crimson', linewidth=1.4)
ax.set_ylabel('柱'); ax2.set_ylabel('线')
ax.set_title("双轴对比（聚簇正态）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
