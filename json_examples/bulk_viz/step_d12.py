"""阶梯图（平方增长）
数据可视化示例（matplotlib）。阶梯折线（事件到达风格）。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = (np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60))
ax.step(np.arange(len(data)), data, where='mid', color='tab:red')
ax.set_title("阶梯图（平方增长）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
