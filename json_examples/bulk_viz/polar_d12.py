"""极坐标玫瑰（平方增长）
数据可视化示例（matplotlib）。极坐标花瓣能量图。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
theta = np.linspace(0, 2 * np.pi, 120)
r = np.abs(np.sin(3 * theta)) * 2 + 0.4
ax = fig.add_subplot(111, projection='polar')
ax.plot(theta, r, color='tab:cyan')
ax.fill(theta, r, alpha=0.25, color='tab:cyan')
ax.set_title("极坐标玫瑰（平方增长）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
