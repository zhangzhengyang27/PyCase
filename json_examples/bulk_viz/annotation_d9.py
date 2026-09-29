"""标注图（锯齿波）
数据可视化示例（matplotlib）。峰值检测与箭头标注。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(y = np.tile(np.linspace(0, 8, 8), 8)[:60] + rng.normal(0, 0.15, 60))
x = np.arange(len(data))
ax.plot(x, data)
peak = data.argmax()
ax.annotate(f'峰值 {{data[peak]:.2f}}', xy=(peak, data[peak]), xytext=(peak - 14, data.max() * 1.05),
            arrowprops=dict(arrowstyle='->', color='red'))
ax.set_title("标注图（锯齿波）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
