"""甘特图：项目排期计划"""
import numpy as np
import matplotlib.pyplot as plt
# 尝试设置中文字体（找不到时中文显示为方块但不影响运行）
try:
    from matplotlib import font_manager
    _zh_fonts = [f.name for f in font_manager.fontManager.ttflist if any(
        k in f.name for k in ("PingFang", "Heiti", "Songti", "Hiragino", "YaHei", "SimHei", "Arial Unicode"))]
    if _zh_fonts:
        plt.rcParams["font.sans-serif"] = [_zh_fonts[0]]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass


tasks = ["需求分析", "UI 设计", "后端开发", "前端开发", "联调测试", "上线部署"]
starts = [0, 2, 4, 5, 9, 12]
durations = [2, 3, 5, 4, 3, 1]
colors = ["#74b9ff", "#a29bfe", "#55efc4", "#fdcb6e", "#fab1a0", "#2ecc71"]

plt.figure(figsize=(10, 6))
for i, (task, start, dur, color) in enumerate(zip(tasks, starts, durations, colors)):
    plt.barh(i, dur, left=start, height=0.5, color=color, edgecolor="white")
    plt.text(start + dur / 2, i, f"{dur}天", ha="center", va="center",
             fontsize=9, color="white")
plt.yticks(range(len(tasks)), tasks)
plt.xlabel("天数")
plt.title("甘特图：项目排期计划")
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("gantt-chart_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")