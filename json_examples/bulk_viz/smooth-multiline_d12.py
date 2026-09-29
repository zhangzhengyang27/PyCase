"""多序列对比（平方增长）
数据可视化示例（matplotlib）。三条平滑曲线对比。
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 12, 200)
for off, color in [(0, 'tab:blue'), (1.5, 'tab:green'), (3, 'tab:red')]:
    ax.plot(x, np.sin(x + off) + off * 0.2, label=f'相位 {off}')
ax.legend()
ax.set_title("多序列对比（平方增长）")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
