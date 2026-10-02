"""火柴杆图（均匀随机）
数据可视化示例（matplotlib）。离散信号火柴杆。
运行后在当前目录生成 'viz_stem_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(rng.uniform(0, 10, 60))
ax.stem(np.arange(len(data)), data, basefmt=' ')
ax.set_title("火柴杆图（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_stem_d4'_preview.png", dpi=110)
print("已生成 'viz_stem_d4'_preview.png")
