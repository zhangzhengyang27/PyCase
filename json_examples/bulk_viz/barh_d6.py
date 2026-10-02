"""水平条形图（周期脉冲）
数据可视化示例（matplotlib）。水平条形（排行风格）。
运行后在当前目录生成 'viz_barh_d6'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(12)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60)))
top = np.sort(data)[-8:]
ax.barh([f'项{i}' for i in range(len(top))], top, color='tab:olive')
ax.set_title("水平条形图（周期脉冲）")
plt.tight_layout()
plt.savefig("'viz_barh_d6'_preview.png", dpi=110)
print("已生成 'viz_barh_d6'_preview.png")
