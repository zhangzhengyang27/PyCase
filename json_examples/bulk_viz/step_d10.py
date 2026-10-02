"""阶梯图（缓升陡降）
数据可视化示例（matplotlib）。阶梯折线（事件到达风格）。
运行后在当前目录生成 'viz_step_d10'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(16)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60))
ax.step(np.arange(len(data)), data, where='mid', color='tab:red')
ax.set_title("阶梯图（缓升陡降）")
plt.tight_layout()
plt.savefig("'viz_step_d10'_preview.png", dpi=110)
print("已生成 'viz_step_d10'_preview.png")
