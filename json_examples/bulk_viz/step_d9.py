"""阶梯图（锯齿波）
数据可视化示例（matplotlib）。阶梯折线（事件到达风格）。
运行后在当前目录生成 'viz_step_d9'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(15)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.tile(np.linspace(0, 8, 8), 8)[:60] + rng.normal(0, 0.15, 60))
ax.step(np.arange(len(data)), data, where='mid', color='tab:red')
ax.set_title("阶梯图（锯齿波）")
plt.tight_layout()
plt.savefig("'viz_step_d9'_preview.png", dpi=110)
print("已生成 'viz_step_d9'_preview.png")
