"""堆叠面积图（平方增长）
数据可视化示例（matplotlib）。三分量堆叠时序。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(60)
data = np.array(y = (np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60))
a = np.abs(data) / data.max() * 4
ax.stackplot(x, a, a * 0.6 + 1, a * 0.3 + 2, labels=['A', 'B', 'C'], alpha=0.8)
ax.legend(loc='upper left')
ax.set_title("堆叠面积图（平方增长）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
