"""面积图（周期脉冲）
数据可视化示例（matplotlib）。填充面积折线。
运行后在当前目录生成 'viz_area_d6'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(12)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60)))
ax.fill_between(np.arange(len(data)), data, alpha=0.55, color='tab:purple')
ax.set_title("面积图（周期脉冲）")
plt.tight_layout()
plt.savefig("'viz_area_d6'_preview.png", dpi=110)
print("已生成 'viz_area_d6'_preview.png")
