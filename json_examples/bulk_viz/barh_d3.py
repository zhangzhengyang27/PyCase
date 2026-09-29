"""水平条形图（指数衰减）
数据可视化示例（matplotlib）。水平条形（排行风格）。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = 8 * np.exp(-np.linspace(0, 4, 60)) + rng.normal(0, 0.12, 60))
top = np.sort(data)[-8:]
ax.barh([f'项{i}' for i in range(len(top))], top, color='tab:olive')
ax.set_title("水平条形图（指数衰减）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
