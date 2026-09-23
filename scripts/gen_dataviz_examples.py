# -*- coding: utf-8 -*-
"""生成数据可视化示例集合 dataviz_examples.json。
示例均依赖 numpy + matplotlib（数据自包含，随机生成或硬编码，无外部文件/网络依赖）。
图表类型参考 matplotlib 官方 Gallery、The Python Graph Gallery、Top 50 Matplotlib 等开源资源。
"""
import json
import os

# 中文字体配置片段（每个示例独立包含，保证可单独运行）
FONT_HELPER = '''# 尝试设置中文字体（找不到时中文显示为方块但不影响运行）
try:
    from matplotlib import font_manager
    _zh_fonts = [f.name for f in font_manager.fontManager.ttflist if any(
        k in f.name for k in ("PingFang", "Heiti", "Songti", "Hiragino", "YaHei", "SimHei", "Arial Unicode"))]
    if _zh_fonts:
        plt.rcParams["font.sans-serif"] = [_zh_fonts[0]]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass
'''

EXAMPLES = []


def add(name, title, description, tags, code):
    """构造并登记一个示例"""
    code = code.strip()
    # 去掉 plt.show()（运行环境无交互窗口，会阻塞子进程）；
    # 改为保存 PNG 到工作目录，由 sidecar 扫描后在前端输出区预览。
    stem = name[:-3]
    code = code.replace(
        "plt.show()",
        f'plt.savefig("{stem}_preview.png", bbox_inches="tight", dpi=110)\nplt.close("all")',
    )
    # 在每个示例头部自动注入中文字体配置
    if "import matplotlib.pyplot as plt" in code and "font_manager" not in code:
        code = code.replace("import matplotlib.pyplot as plt",
                            "import matplotlib.pyplot as plt\n" + FONT_HELPER, 1)
    EXAMPLES.append({
        "id": f"topics_data-analysis_dataviz-{name}",
        "name": name,
        "category": "topics",
        "tags": tags,
        "title": title,
        "description": description,
        "requirements": ["numpy", "matplotlib"],
        "code": code,
    })


# 1. 多系列折线图
add(
    "line-multi-series.py", "多系列折线图",
    "模拟三只股票 60 个交易日的价格随机游走，对比不同资产的价格走势，演示多系列折线图。",
    ["折线图", "时间序列"],
    '''
"""多系列折线图：三只股票价格走势对比"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)
days = np.arange(1, 61)  # 60 个交易日
base = 100
stock_a = base + np.cumsum(np.random.normal(0.5, 2, len(days)))
stock_b = base + np.cumsum(np.random.normal(0.2, 3, len(days)))
stock_c = base + np.cumsum(np.random.normal(-0.1, 1.5, len(days)))

plt.figure(figsize=(10, 6))
plt.plot(days, stock_a, label="股票 A", linewidth=2, color="#2e86de")
plt.plot(days, stock_b, label="股票 B", linewidth=2, color="#e17055")
plt.plot(days, stock_c, label="股票 C", linewidth=2, color="#00b894")
plt.xlabel("交易日")
plt.ylabel("价格")
plt.title("多系列折线图：三只股票的价格走势")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 2. 置信区间填充图
add(
    "line-confidence-band.py", "置信区间填充图",
    "30 次重复实验的均值趋势叠加 ±1σ / ±2σ 阴影区间，演示 fill_between 置信带画法。",
    ["折线图", "置信区间"],
    '''
"""置信区间填充图：均值趋势与置信带"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(7)
x = np.linspace(0, 10, 50)
true_y = np.sin(x) * 5 + 10
trials = 30
ys = np.array([true_y + np.random.normal(0, 1.2, len(x)) for _ in range(trials)])
mean = ys.mean(axis=0)
std = ys.std(axis=0)

plt.figure(figsize=(10, 6))
plt.plot(x, mean, label="均值", color="#0984e3", linewidth=2)
plt.fill_between(x, mean - std, mean + std, alpha=0.25, color="#0984e3", label="±1σ")
plt.fill_between(x, mean - 2 * std, mean + 2 * std, alpha=0.12, color="#0984e3", label="±2σ")
plt.scatter(x, ys[0], s=12, alpha=0.5, color="#b2bec3", label="单次试验")
plt.xlabel("x")
plt.ylabel("y")
plt.title("置信区间填充图：均值与标准差")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 3. 分组柱状图
add(
    "grouped-bar.py", "分组柱状图",
    "三个部门四个季度的销售额分组柱状对比，每个柱子带数值标签，演示分组柱状图。",
    ["柱状图", "对比"],
    '''
"""分组柱状图：各部门季度销售额对比"""
import numpy as np
import matplotlib.pyplot as plt

quarters = ["Q1", "Q2", "Q3", "Q4"]
depts = ["技术部", "市场部", "销售部"]
sales = np.array([
    [120, 135, 148, 160],
    [80, 95, 110, 130],
    [200, 210, 230, 250],
])
x = np.arange(len(quarters))
width = 0.25
colors = ["#2e86de", "#e17055", "#00b894"]

plt.figure(figsize=(10, 6))
for i, (dept, color) in enumerate(zip(depts, colors)):
    plt.bar(x + (i - 1) * width, sales[i], width, label=dept, color=color)
for i in range(len(depts)):
    for j in range(len(quarters)):
        plt.text(x[j] + (i - 1) * width, sales[i][j] + 3, f"{sales[i][j]}",
                 ha="center", fontsize=9)
plt.xticks(x, quarters)
plt.xlabel("季度")
plt.ylabel("销售额（万元）")
plt.title("分组柱状图：各部门季度销售额对比")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 4. 堆叠柱状图
add(
    "stacked-bar.py", "堆叠柱状图",
    "网站流量按直接访问、搜索引擎、社交媒体三个来源逐月堆叠，展示构成变化。",
    ["柱状图", "构成"],
    '''
"""堆叠柱状图：网站流量来源构成"""
import numpy as np
import matplotlib.pyplot as plt

months = ["1月", "2月", "3月", "4月", "5月", "6月"]
direct = [30, 35, 40, 38, 45, 52]
search = [55, 60, 58, 62, 66, 70]
social = [15, 18, 20, 24, 26, 30]

plt.figure(figsize=(10, 6))
plt.bar(months, direct, label="直接访问", color="#2e86de")
plt.bar(months, search, bottom=direct, label="搜索引擎", color="#e17055")
plt.bar(months, social, bottom=np.array(direct) + np.array(search),
        label="社交媒体", color="#00b894")
plt.xlabel("月份")
plt.ylabel("访问量（千次）")
plt.title("堆叠柱状图：网站流量来源构成")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 5. 水平条形排行榜
add(
    "horizontal-bar-rank.py", "水平条形排行榜",
    "商品销量从低到高排列的水平条形图，冠军商品高亮，演示排行榜式条形图。",
    ["柱状图", "排行"],
    '''
"""水平条形图：商品销量排行榜"""
import numpy as np
import matplotlib.pyplot as plt

products = ["无线耳机", "智能手表", "蓝牙音箱", "移动电源", "机械键盘", "游戏鼠标"]
sales = [320, 280, 235, 210, 185, 150]
order = np.argsort(sales)
products = [products[i] for i in order]
sales = sorted(sales)
colors = ["#feca57"] + ["#74b9ff"] * (len(sales) - 1)

plt.figure(figsize=(10, 6))
bars = plt.barh(products, sales, color=colors)
plt.xlabel("销量（件）")
plt.title("水平条形图：商品销量排行榜")
for bar in bars:
    plt.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
             f"{bar.get_width():.0f}", va="center", fontsize=10)
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 6. 气泡图
add(
    "bubble-chart.py", "气泡图",
    "GDP、人口与增长率的四维展示：位置两维、大小映射人口、颜色映射增长率。",
    ["散点图", "多维"],
    '''
"""气泡图：GDP、人口与增长率"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(1)
n = 30
gdp = np.random.uniform(10, 100, n)        # GDP（千亿美元）
population = np.random.uniform(1, 14, n)   # 人口（亿）
growth = np.random.uniform(-2, 8, n)       # 增长率（%）

plt.figure(figsize=(10, 7))
sc = plt.scatter(gdp, population, s=growth * 60 + 30, c=growth, cmap="RdYlGn",
                 alpha=0.7, edgecolors="w")
plt.colorbar(sc, label="增长率（%）")
plt.xlabel("GDP（千亿美元）")
plt.ylabel("人口（亿）")
plt.title("气泡图：GDP、人口与增长率")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 7. 散点密度图
add(
    "scatter-density.py", "散点密度图",
    "2000 个样本的散点分布，通过透明度与颜色感知点的密度，演示大数据散点图。",
    ["散点图", "分布"],
    '''
"""散点密度图：2000 个样本的分布"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(3)
n = 2000
x = np.random.normal(0, 1, n)
y = x * 0.8 + np.random.normal(0, 0.5, n)

plt.figure(figsize=(10, 7))
plt.scatter(x, y, s=8, c="#0984e3", alpha=0.15, edgecolors="none")
plt.xlabel("x")
plt.ylabel("y")
plt.title("散点密度图：2000 个样本的分布")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 8. 直方图与密度曲线
add(
    "histogram-kde.py", "直方图与密度曲线",
    "学生成绩分布直方图叠加卷积平滑的密度曲线，演示分布形态可视化。",
    ["直方图", "分布"],
    '''
"""直方图与密度曲线：学生成绩分布"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(11)
scores = np.concatenate([np.random.normal(72, 12, 400), np.random.normal(55, 8, 100)])

plt.figure(figsize=(10, 6))
counts, bins, patches = plt.hist(scores, bins=30, density=True, alpha=0.6,
                                 color="#2e86de", label="直方图")
# 用滑动平均平滑出密度曲线（避免依赖 scipy）
centers = (bins[:-1] + bins[1:]) / 2
smooth = np.convolve(counts, np.ones(5) / 5, mode="same")
plt.plot(centers, smooth, color="#e17055", linewidth=2.5, label="密度曲线")
plt.xlabel("成绩")
plt.ylabel("密度")
plt.title("直方图与密度曲线：学生成绩分布")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 9. 箱线图
add(
    "boxplot-multi.py", "箱线图",
    "四个班级成绩分布的箱线图对比，包含中位数、四分位距与离群点。",
    ["箱线图", "分布"],
    '''
"""箱线图：四个班级成绩分布对比"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(5)
data = [
    np.random.normal(75, 8, 50),
    np.random.normal(70, 12, 50),
    np.random.normal(82, 6, 50),
    np.random.normal(65, 15, 50),
]
labels = ["一班", "二班", "三班", "四班"]

plt.figure(figsize=(9, 6))
bp = plt.boxplot(data, patch_artist=True, widths=0.5)
plt.xticks(range(1, len(labels) + 1), labels)
colors = ["#74b9ff", "#a29bfe", "#55efc4", "#fab1a0"]
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
plt.ylabel("成绩")
plt.title("箱线图：四个班级成绩分布对比")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
''')

# 10. 带注释热力图
add(
    "heatmap-annotated.py", "带注释热力图",
    "各城市各月平均气温的矩阵热力图，冷暖色映射温度，单元格带数值注释。",
    ["热力图", "矩阵"],
    '''
"""带注释热力图：各城市月均气温"""
import numpy as np
import matplotlib.pyplot as plt

cities = ["北京", "上海", "广州", "成都", "哈尔滨"]
months = ["1月", "3月", "5月", "7月", "9月", "11月"]
temp = np.array([
    [-3, 6, 20, 27, 20, 5],
    [5, 10, 21, 29, 24, 12],
    [14, 18, 26, 29, 27, 20],
    [6, 12, 21, 25, 21, 12],
    [-19, -5, 12, 23, 12, -8],
])

plt.figure(figsize=(9, 6))
im = plt.imshow(temp, cmap="coolwarm", aspect="auto")
plt.colorbar(im, label="平均气温（°C）")
plt.xticks(range(len(months)), months)
plt.yticks(range(len(cities)), cities)
for i in range(len(cities)):
    for j in range(len(months)):
        plt.text(j, i, f"{temp[i, j]:.0f}", ha="center", va="center",
                 color="white" if abs(temp[i, j]) > 15 else "black", fontsize=11)
plt.title("热力图：各城市月均气温")
plt.tight_layout()
plt.show()
''')

# 11. 相关矩阵热力图
add(
    "correlation-matrix.py", "相关矩阵热力图",
    "五个财务指标之间的相关系数矩阵，红蓝发散色映射相关性，带数值标注。",
    ["热力图", "相关性"],
    '''
"""相关矩阵热力图：财务指标相关性"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(21)
n = 200
revenue = np.random.normal(100, 20, n)
profit = revenue * 0.3 + np.random.normal(0, 5, n)
cost = revenue * 0.6 + np.random.normal(0, 8, n)
users = revenue * 0.8 + np.random.normal(0, 15, n)
satisfaction = -cost * 0.02 + np.random.normal(0, 0.5, n)
data = np.vstack([revenue, profit, cost, users, satisfaction])
corr = np.corrcoef(data)
labels = ["营收", "利润", "成本", "用户数", "满意度"]

plt.figure(figsize=(8, 7))
im = plt.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
plt.colorbar(im, label="相关系数")
plt.xticks(range(len(labels)), labels)
plt.yticks(range(len(labels)), labels)
for i in range(len(labels)):
    for j in range(len(labels)):
        plt.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                 color="white" if abs(corr[i, j]) > 0.6 else "black", fontsize=10)
plt.title("相关矩阵热力图：财务指标相关性")
plt.tight_layout()
plt.show()
''')

# 12. 饼图与环形图
add(
    "pie-donut.py", "饼图与环形图",
    "产品线收入占比的经典饼图与环形图并排对比，演示占比可视化两种形态。",
    ["饼图", "占比"],
    '''
"""饼图与环形图：产品线收入占比"""
import numpy as np
import matplotlib.pyplot as plt

labels = ["手机", "电脑", "平板", "穿戴设备", "配件"]
sizes = [35, 28, 15, 12, 10]
colors = ["#2e86de", "#e17055", "#00b894", "#fdcb6e", "#a29bfe"]
explode = (0.05, 0, 0, 0, 0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))
ax1.pie(sizes, labels=labels, colors=colors, explode=explode,
        autopct="%1.1f%%", startangle=90)
ax1.set_title("饼图：产品线收入占比")
ax2.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90,
        wedgeprops=dict(width=0.4, edgecolor="w"))
ax2.set_title("环形图：产品线收入占比")
plt.tight_layout()
plt.show()
''')

# 13. 雷达图
add(
    "radar-chart.py", "雷达图",
    "两款手机在性能、续航、拍照等 6 个维度的能力对比，面积越大优势越明显。",
    ["雷达图", "多维"],
    '''
"""雷达图：两款手机综合能力对比"""
import numpy as np
import matplotlib.pyplot as plt

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
plt.show()
''')

# 14. 甘特图
add(
    "gantt-chart.py", "甘特图",
    "软件项目 6 个阶段的排期计划，用横向条表示任务时长与先后顺序。",
    ["甘特图", "项目管理"],
    '''
"""甘特图：项目排期计划"""
import numpy as np
import matplotlib.pyplot as plt

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
plt.show()
''')

# 15. 双轴组合图
add(
    "dual-axis-combo.py", "双轴组合图",
    "柱状图展示月度销售额、折线图展示同比增长率，主副双 Y 轴同图。",
    ["组合图", "双轴"],
    '''
"""双轴组合图：月度销售额与同比增长率"""
import numpy as np
import matplotlib.pyplot as plt

months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月"]
sales = [120, 135, 128, 150, 168, 175, 190, 210]
growth = [8, 12, -5, 17, 12, 4, 8, 10]

fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.bar(months, sales, color="#74b9ff", alpha=0.8, label="销售额（万元）")
ax1.set_ylabel("销售额（万元）", color="#2e86de")
ax1.set_ylim(0, 250)
ax1.tick_params(axis="y", labelcolor="#2e86de")

ax2 = ax1.twinx()
ax2.plot(months, growth, "o-", color="#e17055", linewidth=2, label="同比增长率（%）")
ax2.set_ylabel("同比增长率（%）", color="#e17055")
ax2.set_ylim(-20, 30)
ax2.tick_params(axis="y", labelcolor="#e17055")
ax2.axhline(0, color="gray", linewidth=0.8, linestyle="--")

plt.title("双轴组合图：月度销售额与同比增长率")
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.tight_layout()
plt.show()
''')

# 16. 对数坐标图
add(
    "log-scale.py", "对数坐标图",
    "数据跨越多个数量级时，线性坐标与对数坐标的效果对比。",
    ["折线图", "对数坐标"],
    '''
"""对数坐标图：线性坐标 vs 对数坐标"""
import numpy as np
import matplotlib.pyplot as plt

x = np.logspace(0, 5, 100)
y1 = x ** 2
y2 = x ** 1.5

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.plot(x, y1, label="y = x²")
ax1.plot(x, y2, label="y = x^1.5")
ax1.set_title("线性坐标")
ax1.set_xlabel("x")
ax1.set_ylabel("y")
ax1.legend()
ax1.grid(alpha=0.3)

ax2.plot(x, y1, label="y = x²")
ax2.plot(x, y2, label="y = x^1.5")
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_title("对数坐标")
ax2.set_xlabel("x（对数）")
ax2.set_ylabel("y（对数）")
ax2.legend()
ax2.grid(alpha=0.3, which="both")
plt.tight_layout()
plt.show()
''')

# 17. 误差棒图
add(
    "error-bar.py", "误差棒图",
    "四种方案的转化率均值与标准误差对比，带误差棒与数值标注。",
    ["误差棒", "对比"],
    '''
"""误差棒图：各方案转化率对比"""
import numpy as np
import matplotlib.pyplot as plt

groups = ["对照组", "方案 A", "方案 B", "方案 C"]
means = [42, 55, 63, 58]
stds = [4, 6, 5, 7]

plt.figure(figsize=(9, 6))
plt.errorbar(range(len(groups)), means, yerr=stds, fmt="o", capsize=6,
             color="#2e86de", ecolor="#e17055", elinewidth=2, markersize=8)
plt.xticks(range(len(groups)), groups)
plt.ylabel("转化率（%）")
plt.title("误差棒图：各方案转化率对比")
plt.grid(axis="y", alpha=0.3)
for i, (m, s) in enumerate(zip(means, stds)):
    plt.text(i, m + s + 1.5, f"{m}±{s}", ha="center", fontsize=9)
plt.ylim(0, 80)
plt.tight_layout()
plt.show()
''')

# 18. 极坐标玫瑰图
add(
    "polar-rose.py", "极坐标玫瑰图",
    "500 个风向样本按 8 个方位统计频数，用极径长度表示频数分布。",
    ["极坐标", "方向"],
    '''
"""极坐标玫瑰图：风向频数分布"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(8)
dirs = np.array([0, 45, 90, 135, 180, 225, 270, 315])
directions = np.random.choice(dirs, size=500)

theta = np.radians(dirs)
counts = [int(np.sum(directions == d)) for d in dirs]

plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)
bars = ax.bar(theta, counts, width=np.radians(45), color="#2e86de",
              alpha=0.75, edgecolor="white")
labels = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
ax.set_xticks(theta)
ax.set_xticklabels(labels)
ax.set_title("极坐标玫瑰图：风向频数分布")
plt.tight_layout()
plt.show()
''')

# 19. 3D 曲面图
add(
    "surface-3d.py", "3D 曲面图",
    "二元函数 z = sin(√(x²+y²)) 的三维曲面，颜色映射高度，经典 3D 可视化。",
    ["3D 图表", "曲面"],
    '''
"""3D 曲面图：z = sin(√(x²+y²))"""
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-5, 5, 80)
y = np.linspace(-5, 5, 80)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X ** 2 + Y ** 2)
Z = np.sin(R) / (R + 0.1)

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X, Y, Z, cmap="viridis", edgecolor="none", alpha=0.9)
fig.colorbar(surf, ax=ax, shrink=0.6, label="z")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D 曲面图：z = sin(√(x²+y²))")
plt.tight_layout()
plt.show()
''')

# 20. 3D 散点图
add(
    "scatter-3d.py", "3D 散点图",
    "120 个样本的三维空间分布，颜色映射 z 值，演示 3D 散点可视化。",
    ["3D 图表", "散点"],
    '''
"""3D 散点图：样本空间分布"""
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(15)
n = 120
x = np.random.normal(0, 1, n)
y = np.random.normal(0, 1, n)
z = x ** 2 + y ** 2 + np.random.normal(0, 0.3, n)

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")
sc = ax.scatter(x, y, z, c=z, cmap="plasma", s=30, alpha=0.8)
fig.colorbar(sc, ax=ax, shrink=0.6, label="z 值")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D 散点图：样本空间分布")
plt.tight_layout()
plt.show()
''')

# 21. 样式表对比
add(
    "style-compare.py", "样式表对比",
    "同一组正弦/余弦数据在不同 matplotlib 风格（default/ggplot/dark/538）下的呈现对比。",
    ["风格", "对比"],
    '''
"""样式表对比：同一数据不同风格"""
import numpy as np
import matplotlib.pyplot as plt

styles = ["default", "ggplot", "dark_background", "fivethirtyeight"]
x = np.linspace(0, 2 * np.pi, 60)

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, style in zip(axes.flat, styles):
    with plt.style.context(style):
        ax.plot(x, np.sin(x), label="sin(x)", linewidth=2)
        ax.plot(x, np.cos(x), label="cos(x)", linewidth=2)
        ax.fill_between(x, np.sin(x), np.cos(x), alpha=0.15)
    ax.set_title(f"Style: {style}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
plt.suptitle("样式表对比：同一数据不同风格")
plt.tight_layout()
plt.show()
''')

# 22. 实时动画折线图
add(
    "animated-line.py", "实时动画折线图",
    "用 FuncAnimation 模拟实时数据流，滑动窗口显示正弦波加噪声的滚动曲线。",
    ["动画", "实时"],
    '''
"""实时动画折线图：滑动窗口数据流"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

np.random.seed(9)
fig, ax = plt.subplots(figsize=(10, 6))
x_data, y_data = [], []
line, = ax.plot([], [], color="#2e86de", linewidth=2)
ax.set_xlim(0, 50)
ax.set_ylim(-3, 3)
ax.grid(alpha=0.3)
ax.set_title("实时动画折线图：正弦波 + 噪声")


def update(frame):
    x_data.append(frame)
    y_data.append(np.sin(frame * 0.3) + np.random.normal(0, 0.15))
    if len(x_data) > 50:
        x_data.pop(0)
        y_data.pop(0)
    line.set_data(x_data, y_data)
    return line,


ani = FuncAnimation(fig, update, frames=range(80), interval=150, blit=True)
plt.show()
''')

# 写出 JSON
out_path = os.path.join(os.path.dirname(__file__), "..", "json_examples", "dataviz_examples.json")
out_path = os.path.normpath(out_path)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"examples": EXAMPLES}, f, ensure_ascii=False, indent=2)
print(f"✅ 已生成 {len(EXAMPLES)} 个数据可视化示例 → {out_path}")
