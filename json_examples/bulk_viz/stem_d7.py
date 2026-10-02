"""火柴杆图（阶梯平台）
数据可视化示例（matplotlib）。离散信号火柴杆。
运行后在当前目录生成 'viz_stem_d7'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(13)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.repeat(rng.uniform(1, 9, 10), 6) + rng.normal(0, 0.2, 60))
ax.stem(np.arange(len(data)), data, basefmt=' ')
ax.set_title("火柴杆图（阶梯平台）")
plt.tight_layout()
plt.savefig("'viz_stem_d7'_preview.png", dpi=110)
print("已生成 'viz_stem_d7'_preview.png")
