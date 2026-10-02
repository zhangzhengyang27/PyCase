"""标注图（阶梯平台）
数据可视化示例（matplotlib）。峰值检测与箭头标注。
运行后在当前目录生成 'viz_annotation_d7'_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(13)
fig, ax = plt.subplots(figsize=(8, 5))
data = np.array(np.repeat(rng.uniform(1, 9, 10), 6) + rng.normal(0, 0.2, 60))
x = np.arange(len(data))
ax.plot(x, data)
peak = data.argmax()
ax.annotate(f'峰值 {data[peak]:.2f}', xy=(peak, data[peak]), xytext=(peak - 14, data.max() * 1.05),
            arrowprops=dict(arrowstyle='->', color='red'))
ax.set_title("标注图（阶梯平台）")
plt.tight_layout()
plt.savefig("'viz_annotation_d7'_preview.png", dpi=110)
print("已生成 'viz_annotation_d7'_preview.png")
