"""火柴杆图（正弦加噪）
数据可视化示例（matplotlib）。离散信号火柴杆。
运行后在当前目录生成 'viz_stem_d1'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(7)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.sin(np.linspace(0, 12, 60)) + rng.normal(0, 0.15, 60))
ax.stem(np.arange(len(data)), data, basefmt=' ')
ax.set_title("火柴杆图（正弦加噪）")
plt.tight_layout()
plt.savefig("'viz_stem_d1'_preview.png", dpi=110)
print("已生成 'viz_stem_d1'_preview.png")
