"""面积图（均匀随机）
数据可视化示例（matplotlib）。填充面积折线。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = rng.uniform(0, 10, 60))
ax.fill_between(np.arange(len(data)), data, alpha=0.55, color='tab:purple')
ax.set_title("面积图（均匀随机）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
