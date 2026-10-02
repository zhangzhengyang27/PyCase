"""标注图（平方增长）
数据可视化示例（matplotlib）。峰值检测与箭头标注。
运行后在当前目录生成 'viz_annotation_d12'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(18)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array((np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60))
x = np.arange(len(data))
ax.plot(x, data)
peak = data.argmax()
ax.annotate(f'峰值 {data[peak]:.2f}', xy=(peak, data[peak]), xytext=(peak - 14, data.max() * 1.05),
            arrowprops=dict(arrowstyle='->', color='red'))
ax.set_title("标注图（平方增长）")
plt.tight_layout()
plt.savefig("'viz_annotation_d12'_preview.png", dpi=110)
print("已生成 'viz_annotation_d12'_preview.png")
