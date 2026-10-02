"""饼图（锯齿波）
数据可视化示例（matplotlib）。占比饼图（含突出块）。
运行后在当前目录生成 'viz_pie_d9'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(15)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.abs(np.array(np.tile(np.linspace(0, 8, 8), 8)[:60] + rng.normal(0, 0.15, 60))[:6])
wedges, texts, autot = ax.pie(data, autopct='%1.0f%%',
        colors=plt.cm.Set2.colors, explode=[0.08] + [0] * 5)
ax.set_title("饼图（锯齿波）")
plt.tight_layout()
plt.savefig("'viz_pie_d9'_preview.png", dpi=110)
print("已生成 'viz_pie_d9'_preview.png")
