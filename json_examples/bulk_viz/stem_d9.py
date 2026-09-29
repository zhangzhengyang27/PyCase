"""火柴杆图（锯齿波）
数据可视化示例（matplotlib）。离散信号火柴杆。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = np.tile(np.linspace(0, 8, 8), 8)[:60] + rng.normal(0, 0.15, 60))
ax.stem(np.arange(len(data)), data, basefmt=' ')
ax.set_title("火柴杆图（锯齿波）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
