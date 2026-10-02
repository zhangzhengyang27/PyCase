"""柱状图（锯齿波）
数据可视化示例（matplotlib）。分箱统计柱状图。
运行后在当前目录生成 'viz_bar_d9'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(15)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.tile(np.linspace(0, 8, 8), 8)[:60] + rng.normal(0, 0.15, 60)
labels = [f'第{i}组' for i in range(0, len(data), 10)]
vals = [data[i:i+10].mean() for i in range(0, len(data), 10)]
ax.bar(labels, vals, color='tab:orange')
ax.set_title("柱状图（锯齿波）")
plt.tight_layout()
plt.savefig("'viz_bar_d9'_preview.png", dpi=110)
print("已生成 'viz_bar_d9'_preview.png")
