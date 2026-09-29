"""柱状图（周期脉冲）
数据可视化示例（matplotlib）。分箱统计柱状图。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = y = np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60))
labels = [f'第{{i}}组' for i in range(0, len(data), 10)]
vals = [data[i:i+10].mean() for i in range(0, len(data), 10)]
ax.bar(labels, vals, color='tab:orange')
ax.set_title("柱状图（周期脉冲）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
