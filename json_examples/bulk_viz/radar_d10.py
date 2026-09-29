"""雷达图（缓升陡降）
数据可视化示例（matplotlib）。多维能力雷达（5 维度）。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
labels = ['速度', '稳定', '覆盖', '成本', '扩展']
vals = np.abs(y = np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60))[:5] / max(1e-9, np.abs(y = np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60))[:5]).max()
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
vals = np.concatenate([vals, vals[:1]]); angles2 = np.concatenate([angles, angles[:1]])
ax = fig.add_subplot(111, projection='polar')
ax.plot(angles2, vals); ax.fill(angles2, vals, alpha=0.3)
ax.set_xticks(angles); ax.set_xticklabels(labels)
ax.set_title("雷达图（缓升陡降）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
