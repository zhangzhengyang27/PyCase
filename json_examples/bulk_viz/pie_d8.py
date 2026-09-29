"""饼图（双峰分布）
数据可视化示例（matplotlib）。占比饼图（含突出块）。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.abs(np.array(y = np.concatenate([rng.normal(2.5, 0.4, 30), rng.normal(7.5, 0.6, 30)]))[:6])
wedges, texts, autot = ax.pie(data, autopct='%1.0f%%',
        colors=plt.cm.Set2.colors, explode=[0.08] + [0] * 5)
ax.set_title("饼图（双峰分布）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
