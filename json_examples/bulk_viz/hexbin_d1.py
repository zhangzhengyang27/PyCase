"""六角分箱（正弦加噪）
数据可视化示例（matplotlib）。二维密度六角分箱。
运行后在当前目录生成 'viz_hexbin_d1'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(7)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 10, 60)
y = np.array(np.sin(np.linspace(0, 12, 60)) + rng.normal(0, 0.15, 60))
ax.hexbin(x, y, gridsize=12, cmap='Blues', mincnt=1)
ax.set_title("六角分箱（正弦加噪）")
plt.tight_layout()
plt.savefig("'viz_hexbin_d1'_preview.png", dpi=110)
print("已生成 'viz_hexbin_d1'_preview.png")
