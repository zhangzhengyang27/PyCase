"""散点图（线性趋势）
数据可视化示例（matplotlib）。两变量相关性散点。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 10, 60)
y = y = np.linspace(2, 9, 60) + rng.normal(0, 0.4, 60)
ax.scatter(x, y, s=18, c=y, cmap='viridis', alpha=0.85)
ax.set_title("散点图（线性趋势）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
