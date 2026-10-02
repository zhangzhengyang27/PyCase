"""雷达图（均匀随机）
数据可视化示例（matplotlib）。多维能力雷达（5 维度）。
运行后在当前目录生成 'viz_radar_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
labels = ['速度', '稳定', '覆盖', '成本', '扩展']
y = rng.uniform(0, 10, 60)
vals = np.abs(y)[:5] / max(1e-9, np.abs(y)[:5].max())
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
vals = np.concatenate([vals, vals[:1]]); angles2 = np.concatenate([angles, angles[:1]])
ax = fig.add_subplot(111, projection='polar')
ax.plot(angles2, vals); ax.fill(angles2, vals, alpha=0.3)
ax.set_xticks(angles); ax.set_xticklabels(labels)
ax.set_title("雷达图（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_radar_d4'_preview.png", dpi=110)
print("已生成 'viz_radar_d4'_preview.png")
