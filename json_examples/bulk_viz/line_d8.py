"""折线图（双峰分布）
数据可视化示例（matplotlib）。单序列折线与标记点。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(y = np.concatenate([rng.normal(2.5, 0.4, 30), rng.normal(7.5, 0.6, 30)])))
y = y = np.concatenate([rng.normal(2.5, 0.4, 30), rng.normal(7.5, 0.6, 30)])
ax.plot(x, y, marker='o', markersize=3, linewidth=1.6, color='tab:blue')
ax.grid(alpha=0.3)
ax.set_title("折线图（双峰分布）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
