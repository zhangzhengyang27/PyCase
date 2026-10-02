"""火柴杆图（平方增长）
数据可视化示例（matplotlib）。离散信号火柴杆。
运行后在当前目录生成 'viz_stem_d12'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(18)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array((np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60))
ax.stem(np.arange(len(data)), data, basefmt=' ')
ax.set_title("火柴杆图（平方增长）")
plt.tight_layout()
plt.savefig("'viz_stem_d12'_preview.png", dpi=110)
print("已生成 'viz_stem_d12'_preview.png")
