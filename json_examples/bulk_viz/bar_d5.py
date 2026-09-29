"""柱状图（聚簇正态）
数据可视化示例（matplotlib）。分箱统计柱状图。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = y = np.concatenate([rng.normal(3, 0.5, 30), rng.normal(7, 0.5, 30)])
labels = [f'第{{i}}组' for i in range(0, len(data), 10)]
vals = [data[i:i+10].mean() for i in range(0, len(data), 10)]
ax.bar(labels, vals, color='tab:orange')
ax.set_title("柱状图（聚簇正态）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
