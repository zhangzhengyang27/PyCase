"""水平条形图（均匀随机）
数据可视化示例（matplotlib）。水平条形（排行风格）。
运行后在当前目录生成 'viz_barh_d4'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(10)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(rng.uniform(0, 10, 60))
top = np.sort(data)[-8:]
ax.barh([f'项{i}' for i in range(len(top))], top, color='tab:olive')
ax.set_title("水平条形图（均匀随机）")
plt.tight_layout()
plt.savefig("'viz_barh_d4'_preview.png", dpi=110)
print("已生成 'viz_barh_d4'_preview.png")
