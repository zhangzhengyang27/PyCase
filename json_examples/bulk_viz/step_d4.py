"""阶梯图（均匀随机）
数据可视化示例（matplotlib）。阶梯折线（事件到达风格）。
运行后在当前目录生成 'viz_step_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(rng.uniform(0, 10, 60))
ax.step(np.arange(len(data)), data, where='mid', color='tab:red')
ax.set_title("阶梯图（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_step_d4'_preview.png", dpi=110)
print("已生成 'viz_step_d4'_preview.png")
