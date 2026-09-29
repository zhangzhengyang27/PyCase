"""热力图（周期脉冲）
数据可视化示例（matplotlib）。矩阵热力图（imshow + 色标）。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60)))
mat = np.outer(data, data)[:20, :]
im = ax.imshow(mat, aspect='auto', cmap='magma')
fig.colorbar(im, ax=ax)
ax.set_title("热力图（周期脉冲）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
