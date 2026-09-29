"""雷达图：两款手机综合能力对比"""
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


dims = ["性能", "续航", "拍照", "屏幕", "重量", "价格"]
phone_a = [90, 75, 88, 85, 70, 60]
phone_b = [80, 92, 70, 78, 85, 90]

angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
values_a = phone_a + phone_a[:1]
values_b = phone_b + phone_b[:1]
angles += angles[:1]

plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)
ax.plot(angles, values_a, "o-", linewidth=2, label="手机 A", color="#2e86de")
ax.fill(angles, values_a, alpha=0.2, color="#2e86de")
ax.plot(angles, values_b, "o-", linewidth=2, label="手机 B", color="#e17055")
ax.fill(angles, values_b, alpha=0.2, color="#e17055")
ax.set_xticks(angles[:-1])
ax.set_xticklabels(dims)
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_title("雷达图：两款手机综合能力对比", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
plt.tight_layout()
plt.savefig("radar-chart_preview.png", bbox_inches="tight", dpi=110)
plt.close("all")