"""饼图（平方增长）
数据可视化示例（matplotlib）。占比饼图（含突出块）。
运行后在当前目录生成 'viz_pie_d12'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(18)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.abs(np.array((np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60))[:6])
wedges, texts, autot = ax.pie(data, autopct='%1.0f%%',
        colors=plt.cm.Set2.colors, explode=[0.08] + [0] * 5)
ax.set_title("饼图（平方增长）")
plt.tight_layout()
plt.savefig("'viz_pie_d12'_preview.png", dpi=110)
print("已生成 'viz_pie_d12'_preview.png")
