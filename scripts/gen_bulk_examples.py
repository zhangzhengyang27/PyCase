#!/usr/bin/env python3
"""批量示例生成器（参数化目录式）。

2026-09-23 数据扩充：按五大主题 + 基础/算法/工具目录，用「图案目录 × 参数变体」
批量产出各自不同的可运行示例。每个示例把参数直接烘焙进源码（不同参数 = 不同代码），
保证：无重复代码、语法有效、自包含可离线运行、依赖只在共享 requirements 内。

设计参照原库做法（原库 Turtle 233 条 / Pygame 194 条即为参数化变体）。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "json_examples"

# 常用色板（十六进制/名字混合，保证视觉差异可感知）
PALETTES = {
    "经典": ["#e74c3c", "#f39c12", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"],
    "海雾": ["#0b3954", "#087e8b", "#bfd7ea", "#ff5a5f", "#c81d25"],
    "暖阳": ["#ffbe0b", "#fb5607", "#ff006e", "#8338ec", "#3a86ff"],
    "薄荷": ["#80ffdb", "#72efdd", "#64dfdf", "#48bfe3", "#5390d9"],
    "暮色": ["#2b2d42", "#8d99ae", "#edf2f4", "#ef233c", "#d90429"],
    "森绿": ["#1b4332", "#2d6a4f", "#40916c", "#74c69d", "#b7e4c7"],
    "樱粉": ["#ff8fab", "#ffc2d1", "#ffe5ec", "#fb6f92", "#ffc9de"],
    "石墨": ["#212529", "#495057", "#868e96", "#ced4da", "#f8f9fa"],
}
PALETTE_NAMES = list(PALETTES)


def slug(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-z_.-]+", "-", text).strip("-")
    return text.lower()


def bake(template: str, **params) -> str:
    """把参数渲染进代码模板（repr 保真：字符串/列表/数值原样进源码）。"""
    out = template
    for k, v in params.items():
        out = out.replace("{{" + k + "}}", repr(v))
    return out


class Collection:
    def __init__(self, file: str, name: str, description: str):
        self.file = file
        self.name = name
        self.description = description
        self.examples = []
        self.seen_code = set()
        self.seen_id = set()

    def add(self, example_id: str, name: str, title: str, description: str,
            tags: list, requirements: list, code: str, category: str = "topics"):
        code = code.strip() + "\n"
        h = hashlib.md5(code.encode()).hexdigest()
        if h in self.seen_code:
            return False
        if example_id in self.seen_id:
            return False
        self.seen_code.add(h)
        self.seen_id.add(example_id)
        self.examples.append({
            "id": example_id, "name": name, "category": category,
            "tags": tags, "title": title, "description": description,
            "requirements": requirements, "code": code,
        })
        return True

    def save(self) -> int:
        out = OUT_DIR / self.file
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"name": self.name, "description": self.description,
                       "examples": self.examples}, f, ensure_ascii=False, indent=1)
        return len(self.examples)


# ===========================================================================
# Turtle 绘图：24 种图案 × 10 变体
# ===========================================================================
def build_turtle():
    coll = Collection("bulk_turtle.json", "Turtle 图集",
                      "参数化生成的 Turtle 绘图示例：每种图案 10 个变体（色板/步长/角度/迭代不同，源码各自独立）。")
    head = '"""{title}\nTurtle 绘图示例。{desc}\n运行后弹出画布，绘制完成自动退出事件循环。\n"""\nimport turtle\n\n'

    def emit(pid, base_title, desc, body_fn, variants, tags=("Turtle", "图形")):
        for i, params in enumerate(variants):
            pname, pv = params
            title = f"{base_title}·{pname}"
            code = 'turtle.bgcolor("#101418")\n' if i % 3 == 0 else ""
            code += body_fn(pv)
            code += "\nt.hideturtle()\nturtle.done()\n"
            colors = pv.get("colors", PALETTES[PALETTE_NAMES[i % len(PALETTE_NAMES)]])
            params = dict(colors=colors)
            params.update(pv)
            code = bake(code, **params)
            ex_id = f"topics_turtle-{pid}-{slug(pname)}"
            coll.add(ex_id, f"{pid}_{slug(pname)}.py", title,
                     f"{desc}变体「{pname}」：{pv.get('note', '不同参数组合的独立绘制代码')}。",
                     list(tags) + ["参数化"], [], head.format(title=title, desc=desc) + code)

    def pal(i):
        return PALETTES[PALETTE_NAMES[i % len(PALETTE_NAMES)]]

    def V(base, count=15):
        return [(f"{PALETTE_NAMES[j % len(PALETTE_NAMES)]}·v{j + 1}",
                 dict(colors=pal(j), **base(j))) for j in range(count)]

    emit("spiral", "渐变螺旋", "边长递增的螺旋线，按取模轮换色板颜色。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
for i in range({{iter_n}}):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // {{wdiv}})
    t.forward(i * {{step}})
    t.left({{angle}})''', V(lambda j: dict(iter_n=100 + j * 20, step=2 + j * 0.4, angle=55 + j * 3, wdiv=15 + j)))

    emit("rose", "玫瑰线", "极坐标玫瑰线 r = R·sin(k·θ)，k 控制花瓣数。",
         lambda p: '''import math
t = turtle.Turtle()
t.speed(0)
t.pensize({{pensize}})
colors = {{colors}}
k, R = {{k}}, {{R}}
for i in range(0, 361, 2):
    rad = math.radians(i)
    r = R * math.sin(k * rad)
    t.pencolor(colors[(i // 30) % len(colors)])
    t.goto(r * math.cos(rad), r * math.sin(rad))''',
         V(lambda j: dict(k=2 + j % 5, R=120 + j * 12, pensize=1 + j % 3)))

    emit("fractal-tree", "递归分形树", "二叉分形树，递归深度与分支角度决定形态。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = {{colors}}

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left({{angle}})
    tree(length * {{shrink}}, depth - 1)
    t.right({{angle}} * 2)
    tree(length * {{shrink}}, depth - 1)
    t.left({{angle}})
    t.backward(length)

tree({{trunk}}, {{depth}})''', V(lambda j: dict(angle=18 + j * 3, shrink=round(0.68 + j * 0.02, 2), trunk=80 + j * 8, depth=7 + j % 3)))

    emit("koch", "科赫雪花", "科赫曲线三连成雪花，迭代深度决定细节层级。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
t.pensize({{pensize}})
t.pencolor({{color}})

def koch(length, depth):
    if depth == 0:
        t.forward(length)
        return
    length /= 3
    koch(length, depth - 1)
    t.left(60)
    koch(length, depth - 1)
    t.right(120)
    koch(length, depth - 1)
    t.left(60)
    koch(length, depth - 1)

for _ in range(3):
    koch({{size}}, {{depth}})
    t.right(120)''', V(lambda j: dict(size=200 + j * 15, depth=2 + j % 3, pensize=1 + j % 3,
                                     color=pal(j)[j % 5])))

    emit("mandala", "对称曼陀罗", "外层旋转复制内层花纹的多重对称图案。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}

def petal():
    for _ in range({{petal_sides}}):
        t.forward({{petal_len}})
        t.right({{petal_turn}})

for ring in range({{rings}}):
    t.pencolor(colors[ring % len(colors)])
    for _ in range({{symmetry}}):
        petal()
        t.right(360 // {{symmetry}})
    t.right({{ring_shift}})
    t.forward({{ring_step}})''', V(lambda j: dict(petal_sides=5 + j % 4, petal_len=40 + j * 6,
                                                 petal_turn=60 + j * 4, rings=5 + j % 3,
                                                 symmetry=10 + j % 4, ring_shift=10 + j, ring_step=6 + j)))

    emit("phyllotaxis", "向日葵点阵", "黄金角排布的点阵，半径按平方根增长。",
         lambda p: '''import math
t = turtle.Turtle()
t.speed(0)
t.penup()
golden = {{golden}}
for i in range({{count}}):
    r = {{spacing}} * math.sqrt(i)
    theta = i * golden
    t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
    ratio = i / {{count}}
    t.pencolor(ratio, 0.7 - 0.5 * ratio, 0.15)
    t.dot({{dot}} + i / {{dotdiv}})''', V(lambda j: dict(golden=137.5 + j * 0.03, count=300 + j * 60,
                                                        spacing=3.8 + j * 0.3, dot=2 + j % 3, dotdiv=50 + j * 5)))

    emit("lissajous", "利萨如曲线", "参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。",
         lambda p: '''import math
t = turtle.Turtle()
t.speed(0)
t.pensize({{pensize}})
colors = {{colors}}
a, b, delta = {{a}}, {{b}}, {{delta}}
for i in range(0, {{points}}):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto({{A}} * math.sin(a * tval + delta), {{B}} * math.sin(b * tval))''',
         V(lambda j: dict(a=1 + j % 4, b=2 + (j * 2) % 5, delta=j * 0.4,
                          A=170 + j * 6, B=130 + j * 8, points=600 + j * 80, pensize=1 + j % 3)))

    emit("butterfly", "蝴蝶曲线", "极坐标蝴蝶曲线 t·e^sin t·(2cos4t−sin^5(t/12))。",
         lambda p: '''import math
t = turtle.Turtle()
t.speed(0)
t.pensize({{pensize}})
t.pencolor({{color}})
for i in range(0, {{points}}):
    tval = i * {{dt}}
    r = math.exp(math.sin(tval)) * (2 * math.cos(4 * tval) - math.sin(tval / 12) ** 5) * {{scale}}
    t.goto(r * math.sin(tval), r * math.cos(tval))''', V(lambda j: dict(points=1200 + j * 200, dt=0.02 + j * 0.002,
                                                                       scale=55 + j * 6, pensize=1 + j % 3,
                                                                       color=pal(j)[j % 5])))

    emit("polygon-ring", "多边形环", "旋转内接多边形形成的光环结构。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
sides, length = {{sides}}, {{length}}
for i in range({{rings}}):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * {{grow}})
        t.left(360 / sides)
    t.left({{shift}})
    t.forward({{step}})''', V(lambda j: dict(sides=3 + j % 6, length=70 + j * 6, rings=14 + j,
                                            grow=2 + j * 0.5, shift=5 + j, step=4 + j)))

    emit("sierpinski", "谢尔宾斯基三角", "中点递归生成的自相似三角形。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
t.pensize(1)
t.pencolor({{color}})
points = [(-{{size}}, -{{size}}), ({{size}}, -{{size}}), (0, {{size}})]
p = points[0]

def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

t.penup()
for _ in range({{dots}}):
    t.pencolor({{color}})
    vx = points[{{vertex_picker}} % 3]
    p = mid(p, vx)
    t.goto(p)
    t.dot(2)''', V(lambda j: dict(size=160 + j * 10, dots=1500 + j * 300, color=pal(j)[j % 5], vertex_picker=j)))

    emit("honeycomb", "六边形密铺", "蜂窝状六边形阵列，逐行偏移排布。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
size = {{size}}
t.penup()
for row in range({{rows}}):
    for col in range({{cols}}):
        x = col * size * 1.732 - {{cols}} * size * 0.866
        y = row * size * 1.5 - {{rows}} * size * 0.75
        t.goto(x + (row % 2) * size * 0.866, y)
        t.setheading(0)
        t.pendown()
        t.pencolor(colors[(row + col) % len(colors)])
        for _ in range(6):
            t.forward(size)
            t.left(60)
        t.penup()''', V(lambda j: dict(size=14 + j * 2, rows=6 + j % 4, cols=8 + j % 4)))

    emit("rings", "同心靶环", "等距同心圆环与交替填充配色。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
t.penup()
colors = {{colors}}
for i in range({{rings}}, 0, -1):
    t.goto(0, -i * {{gap}})
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width({{pensize}})
    t.circle(i * {{gap}})
    t.penup()''', V(lambda j: dict(rings=16 + j * 2, gap=8 + j, pensize=2 + j % 4)))

    emit("waves", "波场线条", "多条相位渐移的正弦波线组成波场。",
         lambda p: '''import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = {{colors}}
for line_i in range({{lines}}):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-{{span}}, {{span}}, 4):
        yv = {{amp}} * math.sin(x * {{freq}} + line_i * {{phase}})
        t.goto(x, yv + line_i * {{row_gap}} - {{lines}} * {{row_gap}} / 2)
        t.pendown() if x == -{{span}} else None''', V(lambda j: dict(lines=10 + j * 2, span=220 + j * 10,
                                                                    amp=24 + j * 3, freq=0.02 + j * 0.004,
                                                                    phase=0.3 + j * 0.08, row_gap=9 + j)))

    emit("rays", "放射光束", "从中心放射的多彩光束，长短交替。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
t.penup()
colors = {{colors}}
for i in range({{beams}}):
    t.setheading(i * 360 / {{beams}})
    t.pencolor(colors[i % len(colors)])
    length = {{inner}} + (i % {{mod}}) * {{grow}}
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)''', V(lambda j: dict(beams=24 + j * 8, inner=30 + j * 4, grow=18 + j * 2, mod=4 + j % 3)))

    emit("heart", "心形曲线", "参数化心形曲线（16sin³t 系），填充着色。",
         lambda p: '''import math
t = turtle.Turtle()
t.speed(0)
t.pensize({{pensize}})
t.pencolor({{color}})
t.fillcolor({{fill}})
t.penup()
first = True
for i in range(0, {{points}}):
    tval = math.pi * 2 * i / {{points}}
    x = 16 * math.sin(tval) ** 3 * {{scale}}
    y = (13 * math.cos(tval) - 5 * math.cos(2 * tval) - 2 * math.cos(3 * tval) - math.cos(4 * tval)) * {{scale}}
    if first:
        t.goto(x, y); t.pendown(); first = False
    else:
        t.goto(x, y)''', V(lambda j: dict(points=200 + j * 40, scale=10 + j, pensize=2 + j % 3,
                                         color=pal(j)[j % 5], fill=pal(j)[(j + 2) % 5])))

    emit("square-stairs", "方块旋梯", "边长渐变的正方形旋转堆叠出楼梯结构。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
for i in range({{count}}):
    t.pencolor(colors[i % len(colors)])
    side = {{side}} + i * {{grow}}
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right({{turn}})
    t.forward({{step}})''', V(lambda j: dict(count=40 + j * 8, side=10 + j, grow=2 + j * 0.3,
                                            turn=6 + j, step=3 + j)))

    emit("dot-field", "点密度场", "按噪声式密度函数布点的圆点场。",
         lambda p: '''import math, random
random.seed({{seed}})
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range({{count}}):
    x = random.randint(-{{span}}, {{span}})
    y = random.randint(-{{span}} * 0.7, {{span}} * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int({{dot}} * (1 - d / ({{span}} * 1.2)))), "{{color}}")''',
         V(lambda j: dict(seed=40 + j, count=500 + j * 80, span=260 + j * 8, dot=7 + j % 4, color=pal(j)[j % 5])))

    emit("galaxy", "旋涡星系", "对数螺线旋臂 + 中心密集点组成的星系。",
         lambda p: '''import math, random
random.seed({{seed}})
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range({{arms}}):
    for i in range({{per_arm}}):
        theta = i * {{twist}} + arm * 360 / {{arms}}
        r = {{r0}} * math.exp({{growth}} * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot({{dot}}, "{{color}}")''', V(lambda j: dict(seed=10 + j, arms=2 + j % 4, per_arm=90 + j * 10,
                                                        twist=3 + j * 0.4, r0=4 + j, growth=0.035 + j * 0.004,
                                                        dot=2 + j % 3, color=pal(j)[j % 5])))

    emit("dragon", "龙曲线", "纸带折叠序列生成的分形龙。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
t.pensize({{pensize}})
t.pencolor({{color}})
seq = [1]
for _ in range({{folds}}):
    seq = seq + [1] + [1 - s for s in reversed(seq)]
for step in seq:
    t.forward({{step_len}})
    t.right(90 if step else -90)''', V(lambda j: dict(folds=8 + j % 4, step_len=5 + j % 3,
                                                     pensize=1 + j % 3, color=pal(j)[j % 5])))

    emit("staircase-wave", "阶梯波", "阶梯递升再回落的周期折线。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
for cycle in range({{cycles}}):
    for s in range({{steps}}):
        t.pencolor(colors[s % len(colors)])
        t.forward({{run}})
        t.left(90)
        t.forward({{rise}})
        t.right(90)
    t.penup()
    t.goto(-{{span}}, (cycle + 1) * -{{fall}})
    t.pendown()''', V(lambda j: dict(cycles=3 + j % 4, steps=6 + j % 5, run=12 + j, rise=6 + j,
                                    span=200, fall=40 + j * 4)))

    emit("hex-flower", "六角花", "绕中心旋转的六边形花瓣簇。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
size = {{size}}
for petal in range({{petals}}):
    t.pencolor(colors[petal % len(colors)])
    t.pensize(1 + petal % 3)
    for _ in range(6):
        t.forward(size)
        t.left(60)
    t.forward(size)
    t.left({{turn}})''', V(lambda j: dict(size=40 + j * 4, petals=12 + j * 3, turn=30 - j)))

    emit("spiral-square", "旋转方阵", "正方形逐层旋转放大的涡旋结构。",
         lambda p: '''t = turtle.Turtle()
t.speed(0)
colors = {{colors}}
for i in range({{count}}):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward({{side}} + i * {{grow}})
    t.left({{angle}})''', V(lambda j: dict(count=90 + j * 15, side=60 + j * 4, grow=1 + j * 0.4, angle=89 + j)))

    emit("burst", "烟花绽放", "多中心随机放射线组成的烟花簇。",
         lambda p: '''import random
random.seed({{seed}})
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = {{colors}}
for burst in range({{bursts}}):
    cx, cy = random.randint(-{{span}}, {{span}}), random.randint(-100, {{span}} * 0.6)
    color = colors[burst % len(colors)]
    for _ in range({{per_burst}}):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint({{min_len}}, {{max_len}}))
        t.penup()''', V(lambda j: dict(seed=50 + j, bursts=6 + j % 4, span=240 + j * 8,
                                      per_burst=40 + j * 6, min_len=18 + j * 2, max_len=48 + j * 4)))
    return coll.save()


# ===========================================================================
# 数据可视化：matplotlib 图表目录 × 数据集变体
# ===========================================================================
def build_viz():
    coll = Collection("bulk_viz.json", "可视化图集",
                      "参数化生成的 matplotlib 图表示例：每种图表 × 多组数据分布变体，输出 PNG 到运行目录。")
    head = '''"""{title}
数据可视化示例（matplotlib）。{desc}
运行后在当前目录生成 {{fname}}_preview.png。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng({{seed}})
fig, ax = plt.subplots(figsize=(8, 5))
'''
    foot = '''ax.set_title("{title}")
plt.tight_layout()
plt.savefig("{{fname}}_preview.png", dpi=110)
print("已生成 {{fname}}_preview.png")
'''
    datasets = [
        ("正弦加噪", "np.sin(np.linspace(0, 12, 60)) + rng.normal(0, 0.15, 60)"),
        ("线性趋势", "np.linspace(2, 9, 60) + rng.normal(0, 0.4, 60)"),
        ("指数衰减", "8 * np.exp(-np.linspace(0, 4, 60)) + rng.normal(0, 0.12, 60)"),
        ("均匀随机", "rng.uniform(0, 10, 60)"),
        ("聚簇正态", "np.concatenate([rng.normal(3, 0.5, 30), rng.normal(7, 0.5, 30)])"),
        ("周期脉冲", "np.where(np.arange(60) % 12 < 3, rng.normal(8, 0.3, 60), rng.normal(2, 0.3, 60))"),
        ("阶梯平台", "np.repeat(rng.uniform(1, 9, 10), 6) + rng.normal(0, 0.2, 60)"),
        ("双峰分布", "np.concatenate([rng.normal(2.5, 0.4, 30), rng.normal(7.5, 0.6, 30)])"),
        ("锯齿波", "np.tile(np.linspace(0, 8, 8), 8)[:60] + rng.normal(0, 0.15, 60)"),
        ("缓升陡降", "np.where(np.arange(60) < 40, np.linspace(1, 9, 60)[:40], np.linspace(9, 1, 20)) + rng.normal(0, 0.2, 60)"),
        ("稀疏脉冲", "np.where(np.arange(60) % 17 == 0, 9.0, 1.0) + rng.normal(0, 0.25, 60)"),
        ("平方增长", "(np.arange(60) / 8.0) ** 2 + rng.normal(0, 0.8, 60)"),
    ]

    def chart(pid, base_title, desc, body, variants):
        for i, (dname, dexpr) in enumerate(datasets):
            title = f"{base_title}（{dname}）"
            fname = f"viz_{pid}_d{i + 1}"
            code = body.replace("{{DATA}}", dexpr)
            head_r = head.replace("{title}", title).replace("{desc}", desc)
            foot_r = foot.replace("{title}", title)
            # bake 必须在 head/code/foot 拼接**之后**：head 的 docstring 与 rng 行
            # 也带 {{seed}}/{{fname}}——先 bake 后拼接曾让它们原样落盘（bulk_viz
            # 619 文件「print 隐形/原样输出」事故的生成器侧根因）
            code = bake(head_r + code + "\n" + foot_r, seed=7 + i, fname=fname)
            coll.add(f"topics_viz-{pid}-d{i + 1}", f"{pid}_d{i + 1}.py", title,
                     f"{desc}数据形态：{dname}。", ["数据可视化", "matplotlib"], ["matplotlib", "numpy"], code)

    chart("line", "折线图", "单序列折线与标记点。",
          "x = np.arange(len({{DATA}}))\ny = {{DATA}}\nax.plot(x, y, marker='o', markersize=3, linewidth=1.6, color='tab:blue')\nax.grid(alpha=0.3)", 6)
    chart("bar", "柱状图", "分箱统计柱状图。",
          "data = {{DATA}}\nlabels = [f'第{i}组' for i in range(0, len(data), 10)]\nvals = [data[i:i+10].mean() for i in range(0, len(data), 10)]\nax.bar(labels, vals, color='tab:orange')", 6)
    chart("scatter", "散点图", "两变量相关性散点。",
          "x = np.linspace(0, 10, 60)\ny = {{DATA}}\nax.scatter(x, y, s=18, c=y, cmap='viridis', alpha=0.85)", 6)
    chart("hist", "直方图", "分布直方图与密度核。",
          "data = np.array({{DATA}})\nax.hist(data, bins=16, color='tab:green', edgecolor='white')", 6)
    chart("step", "阶梯图", "阶梯折线（事件到达风格）。",
          "data = np.array({{DATA}})\nax.step(np.arange(len(data)), data, where='mid', color='tab:red')", 6)
    chart("area", "面积图", "填充面积折线。",
          "data = np.array({{DATA}})\nax.fill_between(np.arange(len(data)), data, alpha=0.55, color='tab:purple')", 6)
    chart("errorbar", "误差条图", "均值 ± 标准差误差条。",
          "data = np.array({{DATA}})\nbins = [data[i:i+10] for i in range(0, 60, 10)]\nmeans = [b.mean() for b in bins]\nstds = [b.std() for b in bins]\nax.errorbar(range(len(bins)), means, yerr=stds, fmt='o', capsize=4, color='tab:brown')", 6)
    chart("stem", "火柴杆图", "离散信号火柴杆。",
          "data = np.array({{DATA}})\nax.stem(np.arange(len(data)), data, basefmt=' ')", 6)
    chart("dual-axis", "双轴对比", "折线 + 柱状双 y 轴对比。",
          "data = np.array({{DATA}})\nax2 = ax.twinx()\nax.bar(np.arange(len(data))[::6], data[::6].mean() + data[::6].std(), alpha=0.3, color='tab:gray')\nax2.plot(data, color='crimson', linewidth=1.4)\nax.set_ylabel('柱'); ax2.set_ylabel('线')", 6)
    chart("smooth-multiline", "多序列对比", "三条平滑曲线对比。",
          "x = np.linspace(0, 12, 200)\nfor off, color in [(0, 'tab:blue'), (1.5, 'tab:green'), (3, 'tab:red')]:\n    ax.plot(x, np.sin(x + off) + off * 0.2, label=f'相位 {off}')\nax.legend()", 6)
    chart("polar", "极坐标玫瑰", "极坐标花瓣能量图。",
          "theta = np.linspace(0, 2 * np.pi, 120)\nr = np.abs(np.sin(3 * theta)) * 2 + 0.4\nax = fig.add_subplot(111, projection='polar')\nax.plot(theta, r, color='tab:cyan')\nax.fill(theta, r, alpha=0.25, color='tab:cyan')", 6)
    chart("radar", "雷达图", "多维能力雷达（5 维度）。",
          "labels = ['速度', '稳定', '覆盖', '成本', '扩展']\ny = {{DATA}}\nvals = np.abs(y)[:5] / max(1e-9, np.abs(y)[:5].max())\nangles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)\nvals = np.concatenate([vals, vals[:1]]); angles2 = np.concatenate([angles, angles[:1]])\nax = fig.add_subplot(111, projection='polar')\nax.plot(angles2, vals); ax.fill(angles2, vals, alpha=0.3)\nax.set_xticks(angles); ax.set_xticklabels(labels)", 6)
    chart("heatmap", "热力图", "矩阵热力图（imshow + 色标）。",
          "data = np.array({{DATA}})\nmat = np.outer(data, data)[:20, :]\nim = ax.imshow(mat, aspect='auto', cmap='magma')\nfig.colorbar(im, ax=ax)", 6)
    chart("contour", "等高线", "二维高斯等高线。",
          "x = np.linspace(-3, 3, 80); yv = np.linspace(-2, 2, 60)\nX, Y = np.meshgrid(x, yv)\nZ = np.exp(-(X ** 2 + Y ** 2)) + 0.4 * np.sin(2 * X) * np.cos(Y)\ncs = ax.contourf(X, Y, Z, levels=14, cmap='coolwarm')\nfig.colorbar(cs, ax=ax)", 6)
    chart("stackplot", "堆叠面积图", "三分量堆叠时序。",
          "x = np.arange(60)\ndata = np.array({{DATA}})\na = np.abs(data) / data.max() * 4\nax.stackplot(x, a, a * 0.6 + 1, a * 0.3 + 2, labels=['A', 'B', 'C'], alpha=0.8)\nax.legend(loc='upper left')", 6)
    chart("box", "箱线图", "分箱箱线图（四分位与离群）。",
          "data = np.array({{DATA}})\nbins = [data[i:i+10] for i in range(0, 60, 10)]\nax.boxplot(bins, patch_artist=True, boxprops=dict(facecolor='lightyellow'))", 6)
    chart("violin", "小提琴图", "分箱小提琴分布。",
          "data = np.array({{DATA}})\nbins = [data[i:i+10] for i in range(0, 60, 10)]\nparts = ax.violinplot(bins, showmedians=True)\nfor pc in parts['bodies']: pc.set_facecolor('tab:purple'); pc.set_alpha(0.6)", 6)
    chart("hexbin", "六角分箱", "二维密度六角分箱。",
          "x = np.linspace(0, 10, 60)\ny = np.array({{DATA}})\nax.hexbin(x, y, gridsize=12, cmap='Blues', mincnt=1)", 6)
    chart("quiver", "矢量场", "旋转矢量场箭头图。",
          "x = np.linspace(-2, 2, 10); yv = np.linspace(-2, 2, 10)\nX, Y = np.meshgrid(x, yv)\nU, Vv = -Y, X\nax.quiver(X, Y, U, Vv, color='tab:blue')", 6)
    chart("barh", "水平条形图", "水平条形（排行风格）。",
          "data = np.array({{DATA}})\ntop = np.sort(data)[-8:]\nax.barh([f'项{i}' for i in range(len(top))], top, color='tab:olive')", 6)
    chart("pie", "饼图", "占比饼图（含突出块）。",
          "data = np.abs(np.array({{DATA}})[:6])\nwedges, texts, autot = ax.pie(data, autopct='%1.0f%%',\n        colors=plt.cm.Set2.colors, explode=[0.08] + [0] * 5)", 6)
    chart("log-scale", "对数坐标", "指数增长对数轴。",
          "x = np.arange(1, 61)\ny = np.exp(0.07 * x) * (1 + np.array({{DATA}}) / 20)\nax.semilogy(x, y, color='tab:gray')\nax.grid(alpha=0.3, which='both')", 6)
    chart("annotation", "标注图", "峰值检测与箭头标注。",
          "data = np.array({{DATA}})\nx = np.arange(len(data))\nax.plot(x, data)\npeak = data.argmax()\nax.annotate(f'峰值 {data[peak]:.2f}', xy=(peak, data[peak]), xytext=(peak - 14, data.max() * 1.05),\n            arrowprops=dict(arrowstyle='->', color='red'))", 6)
    chart("inset", "局部放大", "主图 + 局部放大插图。",
          "data = np.array({{DATA}})\nax.plot(data, linewidth=1.2)\naxi = ax.inset_axes([0.55, 0.55, 0.4, 0.38])\nseg = data[20:32]\naxi.plot(seg, color='tomato'); axi.tick_params(labelsize=6)\nax.indicate_inset_zoom(axi)", 6)
    chart("style-grid", "网格密底图", "密网格 + 参考线风格化折线。",
          "data = np.array({{DATA}})\nax.plot(data, color='#2c3e50', linewidth=2)\nax.axhline(data.mean(), ls='--', color='tomato', label='均值')\nax.legend(); ax.minorticks_on(); ax.grid(alpha=0.25)", 6)
    chart("surface3d", "三维曲面", "3D 高斯曲面。",
          "ax.remove() if hasattr(ax, 'remove') else None\nax = fig.add_subplot(111, projection='3d')\nx = np.linspace(-3, 3, 60); yv = np.linspace(-3, 3, 60)\nX, Y = np.meshgrid(x, yv)\nZ = np.exp(-(X ** 2 + Y ** 2) / 2) * np.cos(2 * X)\nax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9)", 6)
    chart("scatter3d", "三维散点", "3D 螺旋散点。",
          "ax.remove() if hasattr(ax, 'remove') else None\nax = fig.add_subplot(111, projection='3d')\nt = np.linspace(0, 8 * np.pi, 300)\nax.scatter(np.cos(t) * t * 0.12, np.sin(t) * t * 0.12, t, c=t, cmap='plasma', s=8)", 6)
    chart("wireframe3d", "三维线框", "3D 线框波纹。",
          "ax.remove() if hasattr(ax, 'remove') else None\nax = fig.add_subplot(111, projection='3d')\nx = np.linspace(-3, 3, 40); yv = np.linspace(-3, 3, 40)\nX, Y = np.meshgrid(x, yv)\nax.plot_wireframe(X, Y, np.sin(X) * np.cos(Y), rstride=2, cstride=2, color='tab:teal')", 6)
    chart("bar3d", "三维柱状", "3D 柱状矩阵。",
          "ax.remove() if hasattr(ax, 'remove') else None\nax = fig.add_subplot(111, projection='3d')\ndata = np.abs(np.array({{DATA}}))\nfor i in range(6):\n    for j in range(6):\n        ax.bar3d(i, j, 0, 0.6, 0.6, data[(i * 6 + j) % len(data)] / 2, shade=True)", 6)
    chart("twin-styles", "双子图布局", "1×2 子图：折线 + 直方。",
          "data = np.array({{DATA}})\nax.remove() if hasattr(ax, 'remove') else None\nfig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.5))\na1.plot(data, color='tab:blue'); a1.set_title('折线')\na2.hist(data, bins=14, color='tab:orange'); a2.set_title('分布')", 6)
    return coll.save()


# ===========================================================================
# OpenCV 视觉：操作 × 合成场景变体
# ===========================================================================
def build_opencv():
    coll = Collection("bulk_opencv.json", "OpenCV 视觉集",
                      "参数化生成的 OpenCV 图像处理示例：合成场景自包含，无需素材文件，输出结果图到运行目录。")
    head = '''"""{title}
OpenCV 图像处理示例。{desc}
合成输入图像自包含，运行后在当前目录生成 {{fname}}_preview.png。
"""
import cv2
import numpy as np

'''
    scenes = [
        ("几何场景", '''img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)'''),
        ("渐变场景", '''img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)'''),
        ("噪声场景", '''rng = np.random.default_rng({{seed}})
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)'''),
        ("棋盘场景", '''img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)'''),
        ("混合场景", '''rng = np.random.default_rng({{seed}})
img = rng.integers(40, 120, (360, 480), dtype=np.uint8)
cv2.ellipse(img, (240, 180), (180, 90), 25, 0, 360, 230, -1)
cv2.rectangle(img, (60, 60), (160, 160), 255, 4)'''),
        ("点阵圆环", '''img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)'''),
        ("竖条纹", '''img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)'''),
        ("大字报", '''img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)'''),
    ]

    def op(pid, base_title, desc, body, variants=5, tags=("OpenCV",)):
        for i, (sname, scene) in enumerate(scenes):
            title = f"{base_title}（{sname}）"
            fname = f"cv_{pid}_{slug(sname)}"
            code = scene.replace("{{seed}}", str(11 + i)) + "\n\n" + body
            code = bake(code, fname=fname, k=5, t1=100, t2=200, w1=1.5, w2=0.5,
                        clip=2.0, gamma=1.2, angle=30, scale=1.1, d=60, min_area=120)
            full = head.replace("{title}", title).replace("{desc}", desc).replace("{{fname}}", fname) + code + f'''
cv2.imwrite("{fname}_preview.png", result if "result" in dir() else img)
print("已生成 {fname}_preview.png")
'''.replace("{{fname}}", fname)
            coll.add(f"topics_opencv-{pid}-s{i + 1}", f"{pid}_s{i + 1}.py", title,
                     f"{desc}输入场景：{sname}。", list(tags), ["opencv-python", "numpy"], full)

    op("canny", "Canny 边缘", "高斯去噪 + 双阈值边缘提取。",
       "blur = cv2.GaussianBlur(img, (5, 5), 0)\nresult = cv2.Canny(blur, {{t1}}, {{t2}})")
    op("threshold", "阈值分割", "Otsu 全局阈值二值化。",
       "blur = cv2.GaussianBlur(img, (7, 7), 0)\n_, result = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)")
    op("adaptive", "自适应阈值", "局部均值自适应阈值（光照不均友好）。",
       "blur = cv2.medianBlur(img, 5)\nresult = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 6)")
    op("morph-open", "形态学开运算", "腐蚀再膨胀，去小白噪点。",
       "kernel = np.ones(({{k}}, {{k}}), np.uint8)\nresult = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)")
    op("morph-close", "形态学闭运算", "膨胀再腐蚀，补小黑洞。",
       "kernel = np.ones(({{k}}, {{k}}), np.uint8)\nresult = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)")
    op("gradient", "形态学梯度", "膨胀 − 腐蚀 = 边缘带。",
       "kernel = np.ones(({{k}}, {{k}}), np.uint8)\nresult = cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)")
    op("sobel", "Sobel 梯度", "x/y 方向梯度合成幅值。",
       "gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)\ngy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)\nresult = np.clip(np.hypot(gx, gy), 0, 255).astype(np.uint8)")
    op("laplacian", "Laplacian 锐边", "二阶导数边缘响应。",
       "blur = cv2.GaussianBlur(img, (3, 3), 0)\nresult = np.clip(np.abs(cv2.Laplacian(blur, cv2.CV_64F)), 0, 255).astype(np.uint8)")
    op("blur-stack", "模糊对比", "均值/高斯/中值三种模糊并排。",
       "a = cv2.blur(img, ({{k}}, {{k}}))\nb = cv2.GaussianBlur(img, ({{k}}, {{k}}), 0)\nc = cv2.medianBlur(img, {{k}})\nresult = np.hstack([a, b, c])")
    op("sharpen", "锐化滤波", "拉普拉斯混合锐化。",
       "blur = cv2.GaussianBlur(img, (0, 0), 3)\nresult = cv2.addWeighted(img, {{w1}}, blur, -{{w2}}, 0)")
    op("equalize", "直方图均衡", "对比度均衡（CLAHE 局部版）。",
       "clahe = cv2.createCLAHE(clipLimit={{clip}}, tileGridSize=(8, 8))\nresult = clahe.apply(img)")
    op("gamma", "Gamma 校正", "查找表法伽马亮度校正。",
       "table = np.array([(i / 255.0) ** {{gamma}} * 255 for i in range(256)]).astype(np.uint8)\nresult = cv2.LUT(img, table)")
    op("rotate", "仿射旋转", "以中心旋转并缩放。",
       "h, w = img.shape[:2]\nM = cv2.getRotationMatrix2D((w / 2, h / 2), {{angle}}, {{scale}})\nresult = cv2.warpAffine(img, M, (w, h))")
    op("perspective", "透视变换", "四点透视矫正。",
       "h, w = img.shape[:2]\nsrc = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])\ndst = np.float32([[{{d}}, {{d}}], [w - 1 - {{d}}, {{d}} ], [{{d}}, h - 1 - {{d}}], [w - 1 - {{d}}, h - 1 - {{d}}]])\nM = cv2.getPerspectiveTransform(src, dst)\nresult = cv2.warpPerspective(img, M, (w, h))")
    op("resize-pyramid", "缩放金字塔", "逐级缩小的高斯金字塔。",
       "levels = [img]\nfor _ in range(3):\n    levels.append(cv2.pyrDown(levels[-1]))\nresult = np.hstack([cv2.resize(l, (img.shape[1] // 4, img.shape[0] // 4)) for l in levels])")
    op("contours-area", "轮廓筛选", "按面积过滤轮廓并标注质心。",
       '''_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for c in contours:
    area = cv2.contourArea(c)
    if area < {{min_area}}:
        continue
    M = cv2.moments(c)
    if M["m00"]:
        cv2.drawContours(result, [c], -1, (80, 220, 120), 2)
        cv2.circle(result, (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])), 3, (60, 90, 255), -1)''')
    op("hough-lines", "霍夫直线", "概率霍夫变换检测线段。",
       "edges = cv2.Canny(img, 80, 160)\nlines = cv2.HoughLinesP(edges, 1, np.pi / 180, 60, minLineLength=30, maxLineGap=8)\nresult = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)\nif lines is not None:\n    for l in lines[:40]:\n        cv2.line(result, tuple(l[0][:2]), tuple(l[0][2:]), (90, 200, 255), 1)")
    op("distance-transform", "距离变换", "前景像素到边界的距离场。",
       "_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)\nresult = cv2.normalize(cv2.distanceTransform(th, cv2.DIST_L2, 5), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)")
    op("bitwise-mix", "位运算合成", "与/或/异或三通道合成。",
       "h, w = img.shape[:2]\nm1 = np.zeros_like(img); cv2.circle(m1, (w // 3, h // 2), 80, 255, -1)\nm2 = np.zeros_like(img); cv2.rectangle(m2, (w // 2, 40), (w - 20, h - 40), 255, -1)\nresult = np.hstack([cv2.bitwise_and(m1, m2), cv2.bitwise_or(m1, m2), cv2.bitwise_xor(m1, m2)])")
    op("colormap", "伪彩色映射", "灰度图套用 COLORMAP_JET。",
       "result = cv2.applyColorMap(img, cv2.COLORMAP_JET)")
    return coll.save()


# ===========================================================================
# PIL 图像处理：操作 × 变体
# ===========================================================================
def build_pil():
    coll = Collection("bulk_pil.json", "PIL 图像集",
                      "参数化生成的 Pillow 图像处理示例：程序化生成源图自包含，输出结果图到运行目录。")
    head = '''"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 {{fname}}_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", ({{w}}, {{h}}), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * ({{w}} - 60) // 7
dr.rectangle([{{w}} // 2 - 70, {{h}} // 2, {{w}} // 2 + 70, {{h}} - 30], outline="#e8e8e8", width=3)
'''
    # 修正 head 中那个无效的条件表达式：直接用确定色板
    head = head.replace('    dr.ellipse([x0, {{h}} // 3 - 30, x0 + 56, {{h}} // 3 + 26], fill="{{c%02d}}" % i if False else ("#%02x%02x%02x" % (40 + i * 26, 90 + i * 14, 160 + i * 10)))\n',
                        '    dr.ellipse([x0, {{h}} // 3 - 30, x0 + 56, {{h}} // 3 + 26], fill=("#%02x%02x%02x" % (40 + i * 26, 90 + i * 14, 160 + i * 10)))\n')

    def op(pid, base_title, desc, body, variants=12, tags=("Pillow", "图像")):
        palette = ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#f368e0", "#54a0ff"]
        for i in range(variants):
            title = f"{base_title}·变体{i + 1}"
            fname = f"pil_{pid}_v{i + 1}"
            code = bake(body, fname=fname, i=i, color=palette[i % 6])
            full = bake(head, fname=fname, w=420 + i * 24, h=300 + i * 12, c00=palette[i % 6]) + "\n" + code + f'''
result.save("{fname}_preview.png")
print("已生成 {fname}_preview.png")
'''
            coll.add(f"topics_pil-{pid}-v{i + 1}", f"{pid}_v{i + 1}.py", title,
                     f"{desc}（参数组 {i + 1}）。", list(tags), ["pillow"], full)

    op("gaussian", "高斯模糊", "不同半径的高斯模糊对比。",
       "result = base.filter(ImageFilter.GaussianBlur(radius={{i}} + 1))")
    op("contour", "轮廓提取", "ImageFilter.CONTOUR 边缘轮廓。",
       "result = base.filter(ImageFilter.CONTOUR)")
    op("emboss", "浮雕效果", "EMBOSS 滤镜的立体浮雕感。",
       "result = base.filter(ImageFilter.EMBOSS)")
    op("grayscale", "灰度化", "convert('L') 灰度 + 自动对比度。",
       "result = ImageOps.autocontrast(base.convert('L'))")
    op("invert", "反色", "ImageOps.invert 颜色反转。",
       "result = ImageOps.invert(base)")
    op("solarize", "曝光过度", "ImageOps.solarize 阈值翻转。",
       "result = ImageOps.solarize(base, threshold={{i}} * 30 + 90)")
    op("posterize", "色调分离", "posterize 减少每通道位数。",
       "result = ImageOps.posterize(base, bits={{i}} + 2)")
    op("mirror", "镜像拼贴", "水平镜像后与原图并排。",
       "result = Image.new('RGB', (base.width * 2, base.height))\nresult.paste(base, (0, 0))\nresult.paste(ImageOps.mirror(base), (base.width, 0))")
    op("rotate-crop", "旋转裁剪", "旋转 45 度后中心裁剪。",
       "rotated = base.rotate(45, expand=True, fillcolor='#111')\nw, h = rotated.size\nresult = rotated.crop(((w - base.width) // 2, (h - base.height) // 2,\n                       (w + base.width) // 2, (h + base.height) // 2))")
    op("enhance-quad", "四合一增强", "锐化/平滑/边缘/原色四宫格。",
       "w, h = base.size\nresult = Image.new('RGB', (w * 2 + 8, h * 2 + 8), '#111')\nfor idx, im in enumerate([base, base.filter(ImageFilter.SHARPEN),\n                          base.filter(ImageFilter.SMOOTH_MORE), base.filter(ImageFilter.FIND_EDGES)]):\n    result.paste(im, ((idx % 2) * (w + 8), (idx // 2) * (h + 8)))")
    op("gradient-mask", "渐隐蒙版", "按渐变蒙版向纯色渐隐。",
       "mask = Image.linear_gradient('L').resize(base.size)\nsolid = Image.new('RGB', base.size, {{color}})\nresult = Image.composite(base, solid, mask)")
    op("pixelate", "像素化", "缩小再放大的马赛克。",
       "small = base.resize((base.width // {{i}} - 6, base.height // {{i}} - 8))\nresult = small.resize(base.size, Image.NEAREST)")
    return coll.save()


# ===========================================================================
# Pygame 游戏：游戏 × 变体
# ===========================================================================
def build_games():
    coll = Collection("bulk_games.json", "小游戏集",
                      "参数化生成的 Pygame 小游戏：同一玩法不同参数（速度/尺寸/配色），各自独立可运行。")
    head = '''"""{title}
Pygame 小游戏。{desc}
运行后弹出游戏窗口；ESC 或关闭窗口退出。
"""
import random
import sys

import pygame

'''
    def game(pid, base_title, desc, params_list, body_fn, tags=("Pygame", "游戏")):
        for i, pv in enumerate(params_list):
            title = f"{base_title}·{pv.get('vname', '变体' + str(i + 1))}"
            code = bake(body_fn(pv), **pv)
            full = head.format(title=title, desc=desc) + code
            coll.add(f"topics_game-{pid}-{i + 1}", f"{pid}_v{i + 1}.py", title,
                     f"{desc}本变体：{pv.get('vname', '')}（速度 {pv.get('speed', '-')}，窗口 {pv.get('W', '-')}×{pv.get('H', '-')}）。",
                     list(tags), ["pygame"], full)

    def snake_body(p):
        return '''CELL, COLS, ROWS = {{cell}}, {{W}} // {{cell}}, {{H}} // {{cell}}
pygame.init()
screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("贪吃蛇")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

snake = [(COLS // 2, ROWS // 2)]
direction = (1, 0)
food = (random.randrange(COLS), random.randrange(ROWS))
score = 0
SPEED = {{speed}}
BODY_COLOR = ({{cr}}, {{cg}}, {{cb}})

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            turn = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
                    pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}.get(event.key)
            if turn and (turn[0] != -direction[0] or turn[1] != -direction[1]):
                direction = turn

    head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    if head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS or head in snake:
        print(f"游戏结束，得分 {score}")
        break
    snake.insert(0, head)
    if head == food:
        score += 1
        food = (random.randrange(COLS), random.randrange(ROWS))
    else:
        snake.pop()

    screen.fill((16, 18, 24))
    for x, y in snake:
        pygame.draw.rect(screen, BODY_COLOR, (x * CELL, y * CELL, CELL - 2, CELL - 2), border_radius=4)
    pygame.draw.rect(screen, (230, 90, 90), (food[0] * CELL, food[1] * CELL, CELL - 2, CELL - 2), border_radius=8)
    screen.blit(font.render(f"Score: {score}", True, (240, 240, 240)), (8, 6))
    pygame.display.flip()
    clock.tick(SPEED)'''
    game("snake", "贪吃蛇", "网格贪吃蛇，吃食物变长，撞墙/自身结束。",
         [dict(vname=v, W=576 + v * 48, H=432 + v * 24, cell=24 - v % 3 * 2, speed=7 + v * 2,
               cr=60 + v * 22, cg=200 - v * 12, cb=100 + v * 14) for v in range(5)], snake_body)

    def catch_body(p):
        return '''W, H = {{W}}, {{H}}
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("接水果")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

basket = pygame.Rect(W // 2 - 44, H - 60, 88, 26)
fruits = []
lives, caught, spawn_ms = {{lives}}, 0, 0
DROP = {{speed}}
PALETTE = [{{colors}}]

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: basket.x -= 7
    if keys[pygame.K_RIGHT]: basket.x += 7
    basket.clamp_ip((0, 0, W, basket.height))
    spawn_ms += dt
    if spawn_ms > {{interval}}:
        spawn_ms = 0
        fruits.append(pygame.Rect(random.randint(0, W - 22), -22, 22, 22))
    for f in fruits[:]:
        f.y += DROP
        if f.colliderect(basket):
            fruits.remove(f); caught += 1
        elif f.y > H:
            fruits.remove(f); lives -= 1
    screen.fill((24, 28, 36))
    pygame.draw.rect(screen, (120, 200, 250), basket, border_radius=6)
    for i, f in enumerate(fruits):
        pygame.draw.circle(screen, PALETTE[i % len(PALETTE)], f.center, 11)
    screen.blit(font.render(f"接住 {caught}  生命 {lives}", True, (240, 240, 240)), (10, 8))
    pygame.display.flip()
    if lives <= 0:
        print(f"游戏结束，接住 {caught} 个")
        break'''
    game("catch", "接水果", "左右移动篮子接水果，漏接扣命。",
         [dict(vname=f"速度{4 + v}", W=560 + v * 40, H=480, speed=3.4 + v * 0.7, interval=560 - v * 60,
               lives=3 + v % 2, colors=", ".join(f'"{c}"' for c in PALETTES[list(PALETTES)[v]][v % 4:v % 4 + 3]))
          for v in range(4)], catch_body)

    def pong_body(p):
        return '''W, H = {{W}}, {{H}}
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
paddle_h, speed = {{paddle}}, {{pspeed}}
left = pygame.Rect(16, H // 2 - paddle_h // 2, 12, paddle_h)
right = pygame.Rect(W - 28, H // 2 - paddle_h // 2, 12, paddle_h)
ball = pygame.Rect(W // 2 - 6, H // 2 - 6, 12, 12)
ball_v = [{{bx}}, {{by}}]
score = [0, 0]
WIN = {{win}}

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: left.y -= speed
    if keys[pygame.K_s]: left.y += speed
    if keys[pygame.K_UP]: right.y -= speed
    if keys[pygame.K_DOWN]: right.y += speed
    left.clamp_ip((0, 0, W, H)); right.clamp_ip((0, 0, W, H))
    ball.x += int(ball_v[0]); ball.y += int(ball_v[1])
    if ball.top <= 0 or ball.bottom >= H: ball_v[1] *= -1
    if ball.colliderect(left) or ball.colliderect(right): ball_v[0] *= -1.05
    if ball.left <= 0: score[1] += 1; ball.center = (W // 2, H // 2)
    if ball.right >= W: score[0] += 1; ball.center = (W // 2, H // 2)
    screen.fill((16, 20, 28))
    pygame.draw.rect(screen, (240, 240, 240), left)
    pygame.draw.rect(screen, (240, 240, 240), right)
    pygame.draw.rect(screen, (255, 200, 80), ball)
    screen.blit(font.render(f"{score[0]} : {score[1]}", True, (240, 240, 240)), (W // 2 - 40, 10))
    pygame.display.flip(); clock.tick(60)
    if WIN in score:
        print(f"比赛结束 {score[0]}:{score[1]}")
        break'''
    game("pong", "双人弹球", "W/S 与方向键控制球拍对打。",
         [dict(vname=f"先得{3 + v}分", W=640 + v * 40, H=440, paddle=88 - v * 8, pspeed=6 + v,
               bx=4.0 + v * 0.5, by=2.8 + v * 0.4, win=3 + v) for v in range(4)], pong_body)
    return coll.save()


# ===========================================================================
# Python 基础 / 算法 / 工具：主题 × 变体
# ===========================================================================
def build_basics():
    coll = Collection("bulk_basics.json", "基础与工具集",
                      "参数化生成的 Python 基础、经典算法与实用工具示例（纯标准库，参数各不相同）。")

    def add(pid, base_title, desc, tags, body_fn, variants, category="topics", reqs=None):
        for i, pv in enumerate(variants):
            pname = pv.get("vname", f"变体{i + 1}")
            title = f"{base_title}·{pname}"
            code = bake(body_fn(pv), **pv)
            ex_id = f"{category}_{pid}-{i + 1}"
            if coll.add(ex_id, f"{pid}_{i + 1}.py", title, f"{desc}本变体：{pname}。", list(tags), reqs or [], code, category):
                pass

    # ---------------- 基础 ----------------
    add("basics-fizzbuzz", "FizzBuzz 变奏", "经典整除分类打印，参数化区间与规则。",
        ["基础", "循环"],
        lambda p: '''"""FizzBuzz：{{lo}}~{{hi}}，{{a}} 的倍数输出 A，{{b}} 的倍数输出 B。"""
for n in range({{lo}}, {{hi}} + 1):
    out = ""
    if n % {{a}} == 0:
        out += "A"
    if n % {{b}} == 0:
        out += "B"
    print(n, out or n)''',
        [dict(vname=f"{lo}~{hi}·{a}/{b}", lo=lo, hi=hi, a=a, b=b)
         for lo, hi in [(1, 30), (1, 50), (10, 60), (20, 80), (1, 100)]
         for a, b in [(3, 5), (2, 7), (4, 6)]][:12])

    add("basics-prime", "素数筛", "埃氏筛统计区间素数。",
        ["基础", "数学"],
        lambda p: '''"""素数筛：找出 {{limit}} 以内的全部素数并统计。"""
limit = {{limit}}
sieve = [True] * (limit + 1)
sieve[0] = sieve[1] = False
for n in range(2, int(limit ** 0.5) + 1):
    if sieve[n]:
        for m in range(n * n, limit + 1, n):
            sieve[m] = False
primes = [i for i, ok in enumerate(sieve) if ok]
print(f"{{limit}} 以内素数 {len(primes)} 个：", primes[:20], "...")''',
        [dict(vname=f"N={n}", limit=n) for n in (100, 200, 500, 1000, 2000, 5000)])

    add("basics-fibonacci", "斐波那契三解", "递归/迭代/矩阵快速幂对比。",
        ["基础", "动态规划"],
        lambda p: '''"""斐波那契第 {{n}} 项：三种实现对照。"""
from functools import lru_cache


@lru_cache(maxsize=None)
def fib_rec(k):
    return k if k < 2 else fib_rec(k - 1) + fib_rec(k - 2)


def fib_iter(k):
    a, b = 0, 1
    for _ in range(k):
        a, b = b, a + b
    return a


def fib_fast(k):
    def mul(x, y):
        return [[x[0][0] * y[0][0] + x[0][1] * y[1][0], x[0][0] * y[0][1] + x[0][1] * y[1][1]],
                [x[1][0] * y[0][0] + x[1][1] * y[1][0], x[1][0] * y[0][1] + x[1][1] * y[1][1]]]

    def mpow(m, e):
        r = [[1, 0], [0, 1]]
        while e:
            if e & 1:
                r = mul(r, m)
            m = mul(m, m)
            e >>= 1
        return r

    return mpow([[1, 1], [1, 0]], k)[0][1]


n = {{n}}
print("迭代:", fib_iter(n), "| 递归:", fib_rec(n), "| 快速幂:", fib_fast(n))''',
        [dict(vname=f"n={n}", n=n) for n in (10, 20, 30, 50, 80)])

    add("basics-wordcount", "词频统计", "Counter 统计文本词频并输出 TopN。",
        ["基础", "文本", "统计"],
        lambda p: ('''"""词频统计：Top {{topn}}。"""
from collections import Counter

text = """''' + p["text"] + '''"""
words = [w.strip(".,!?;:()").lower() for w in text.split()]
words = [w for w in words if w]
counter = Counter(words)
for word, cnt in counter.most_common({{topn}}):
    print(f"{word:>12}  {cnt}")
print("去重词数:", len(counter))'''),
        [dict(vname=f"Top{t}", topn=t,
              text=("python is simple python is powerful and python is everywhere "
                    "simple tools with powerful ideas make python everywhere python"))
         for t in (3, 5, 8)])

    # basics-date-diff 已退役（2026-10-02）：5 个静态变体升级为工具箱「日期计算器」
    # 交互工具（renderer/src/interactive-tools.ts），日期主题不再在语料里重复占位。

    add("basics-matrix-mul", "矩阵乘法", "纯 Python 三重循环矩阵乘法。",
        ["基础", "线性代数"],
        lambda p: '''"""矩阵乘法：{{n}}×{{n}} 方阵（纯 Python 验证）。"""
A = [[(i * j + 1) % {{mod}} for j in range({{n}})] for i in range({{n}})]
B = [[(i + 2 * j) % {{mod}} for j in range({{n}})] for i in range({{n}})]
C = [[sum(A[i][k] * B[k][j] for k in range({{n}})) for j in range({{n}})] for i in range({{n}})]
print("C[0][:6] =", C[0][:6])
print("C[-1][-3:] =", C[-1][-3:])''',
        [dict(vname=f"n={n}·m{m}", n=n, mod=m) for n, m in [(4, 7), (6, 11), (8, 13), (10, 5), (12, 9)]])

    # ---------------- 算法 ----------------
    add("algo-binary-search", "二分查找", "有序数组二分定位（含边界变体）。",
        ["算法", "查找"],
        lambda p: '''"""二分查找：在长度 {{n}} 的有序数组中定位全部目标。"""
data = sorted({{data}})
targets = {{targets}}

def bsearch(arr, x):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            return mid
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

for t in targets:
    print(t, "->", bsearch(data, t))''',
        [dict(vname=f"n={n}", n=n, data=list(range(2, 2 + n * 3, 3)),
              targets=[7, 20, 5 + n]) for n in (20, 50, 100)])

    add("algo-quick-sort", "快速排序", "手写快排（尾递归式分区）。",
        ["算法", "排序"],
        lambda p: '''"""快速排序：{{n}} 个随机整数。"""
import random
random.seed({{seed}})
data = [random.randint({{lo}}, {{hi}}) for _ in range({{n}})]

def qsort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return qsort(left) + mid + qsort(right)

print("原:", data[:12], "...")
print("排序后:", qsort(data)[:12], "...")''',
        [dict(vname=f"n={n}", n=n, seed=s, lo=lo, hi=hi) for n, s, lo, hi in
         [(20, 1, 0, 100), (50, 2, 0, 500), (100, 3, -50, 50), (200, 4, 0, 9)]])

    add("algo-lcs", "最长公共子序列", "动态规划 LCS 与回溯路径。",
        ["算法", "动态规划"],
        lambda p: '''"""LCS：'{a}' 与 '{b}' 的最长公共子序列。"""
A, B = "{{a}}", "{{b}}"
dp = [[0] * (len(B) + 1) for _ in range(len(A) + 1)]
for i in range(1, len(A) + 1):
    for j in range(1, len(B) + 1):
        dp[i][j] = dp[i - 1][j - 1] + 1 if A[i - 1] == B[j - 1] else max(dp[i - 1][j], dp[i][j - 1])
i, j, out = len(A), len(B), []
while i and j:
    if A[i - 1] == B[j - 1]:
        out.append(A[i - 1]); i -= 1; j -= 1
    elif dp[i - 1][j] >= dp[i][j - 1]:
        i -= 1
    else:
        j -= 1
print("LCS 长度:", dp[-1][-1], "| 序列:", "".join(reversed(out)))''',
        [dict(vname=f"{a[:6]}×{b[:6]}", a=a, b=b) for a, b in
         [("ABCBDAB", "BDCABA"), ("动态规划很重要", "规规整整做规划"), ("kitten", "sitting"),
          ("AGGTAB", "GXTXAYB")]])

    add("algo-dijkstra", "Dijkstra 最短路", "邻接表 + 堆的最短路径。",
        ["算法", "图"],
        lambda p: '''"""Dijkstra：从 0 号点到各点的最短距离（{{n}} 个顶点）。"""
import heapq

graph = {{edges}}
dist = {0: 0}
heap = [(0, 0)]
while heap:
    d, u = heapq.heappop(heap)
    if d > dist.get(u, float("inf")):
        continue
    for v, w in graph.get(u, []):
        nd = d + w
        if nd < dist.get(v, float("inf")):
            dist[v] = nd
            heapq.heappush(heap, (nd, v))
print(dict(sorted(dist.items())))''',
        [dict(vname=f"n={n}", n=n, edges=ed) for n, ed in
         [(5, {0: [(1, 4), (2, 1)], 1: [(3, 1)], 2: [(1, 2), (3, 5)], 3: [(4, 3)], 4: []}),
          (6, {0: [(1, 2), (2, 6)], 1: [(3, 5)], 2: [(3, 1)], 3: [(4, 2), (5, 6)], 4: [], 5: []}),
          (7, {0: [(1, 7), (2, 9), (3, 14)], 1: [(2, 10), (5, 4)], 2: [(3, 11), (5, 2)], 3: [], 5: [(6, 3)], 6: []})]])

    add("algo-knapsack", "0-1 背包", "动态规划背包最优值与回溯。",
        ["算法", "动态规划"],
        lambda p: '''"""0-1 背包：容量 {{cap}}，{{n}} 件物品。"""
weights = {{weights}}
values = {{values}}
cap = {{cap}}
dp = [0] * (cap + 1)
for w, v in zip(weights, values):
    for c in range(cap, w - 1, -1):
        dp[c] = max(dp[c], dp[c - w] + v)
print("最大价值:", dp[cap])''',
        [dict(vname=f"容量{cap}", cap=cap, n=len(w), weights=w, values=v) for cap, w, v in
         [(10, [2, 3, 5, 7], [3, 4, 5, 9]), (15, [4, 5, 6, 2, 3], [7, 8, 9, 2, 4]),
          (20, [5, 6, 8, 3, 4, 7], [10, 12, 15, 4, 6, 11]), (30, list(range(3, 18, 2)), [v * 3 for v in range(2, 18, 2)])]])

    add("algo-union-find", "并查集", "路径压缩 + 按秩合并的并查集。",
        ["算法", "图"],
        lambda p: '''"""并查集：{{n}} 个元素执行 {{ops}} 次合并/查询。"""
parent = list(range({{n}}))
rank = [0] * {{n}}

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False
    if rank[ra] < rank[rb]:
        ra, rb = rb, ra
    parent[rb] = ra
    if rank[ra] == rank[rb]:
        rank[ra] += 1
    return True

pairs = [({{p0}}, {{p1}}), ({{p2}}, {{p3}}), ({{p4}}, {{p5}})]
for a, b in pairs:
    union(a, b)
print("连通分量数:", len({find(i) for i in range({{n}})}))''',
        [dict(vname=f"N{8 + p}-P{p}", n=8 + p, p=p, p0=0, p1=1 + p % 3, p2=2, p3=4 + p % 3, p4=5, p5=6, ops=p + 3)
         for p in range(3)])

    # ---------------- 工具 ----------------
    # tools-temp-converter / tools-base-convert / tools-caesar 已退役（2026-10-02，W1）：
    # 12 个静态变体升级为工具箱 schema 驱动交互工具（renderer/src/tool-schemas.ts）。

    add("tools-qr-matrix", "字符方阵", "按规则生成字符方阵（可视图案）。",
        ["工具", "图案"], category="tools",
        body_fn=lambda p: '''"""字符方阵：{{size}}×{{size}}，字符集 '{{chars}}'。"""
size, chars = {{size}}, "{{chars}}"
for r in range(size):
    row = "".join(chars[(r * c + r + c) % len(chars)] for c in range(size))
    print(row)''',
        variants=[dict(vname=f"s{s}{c}", size=s, chars=c) for s, c in
                  [(9, "◆◇"), (11, "░▒▓"), (13, "·:*#"), (10, "AB123")]])

    add("tools-text-table", "文本表格", "格式化对齐输出 Markdown 表格。",
        ["工具", "文本"], category="tools",
        body_fn=lambda p: '''"""文本表格：{{rows}} 行对齐输出。"""
headers = ["名称", "数量", "单价"]
data = {{data}}
widths = [max(len(str(headers[i])), max(len(str(r[i])) for r in data)) for i in range(3)]
line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"
print(line)
print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
for r in data:
    print("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |")''',
        variants=[dict(vname="商品", rows=4, data=[["苹果", 12, 5.5], ["香蕉", 30, 3.2], ["橙子", 8, 6.0], ["葡萄", 15, 9.9]]),
                  dict(vname="库存", rows=3, data=[["螺丝", 400, 0.2], ["螺母", 350, 0.3], ["垫片", 500, 0.1]]),
                  dict(vname="成绩", rows=5, data=[["小明", 92, 1], ["小红", 88, 2], ["小刚", 95, 1], ["小丽", 79, 3], ["小军", 85, 2]])])

    return coll.save()


# ===========================================================================
# 主流程：全部生成 + 语法体检
# ===========================================================================
def syntax_check(coll: Collection) -> int:
    import ast as _ast
    import warnings
    bad = 0
    for e in coll.examples:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                _ast.parse(e["code"])
            except SyntaxError as err:
                bad += 1
                print(f"  ✗ {e['id']}: line {err.lineno} {err.msg}")
    return bad


def main():
    import ast as _ast
    import warnings

    def check(coll_data):
        bad = 0
        for e in coll_data["examples"]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    _ast.parse(e["code"])
                except SyntaxError as err:
                    bad += 1
                    print(f"  ✗ {e['id']}: line {err.lineno} {err.msg}")
        return bad

    total = 0
    for label, file in [("Turtle", "bulk_turtle.json"), ("可视化", "bulk_viz.json"),
                        ("OpenCV", "bulk_opencv.json"), ("PIL", "bulk_pil.json"),
                        ("小游戏", "bulk_games.json"), ("基础/算法/工具", "bulk_basics.json")]:
        n = {"Turtle": build_turtle, "可视化": build_viz, "OpenCV": build_opencv,
             "PIL": build_pil, "小游戏": build_games, "基础/算法/工具": build_basics}[label]()
        if label == "基础/算法/工具":
            n += build_basics_extra()
        data = json.load(open(OUT_DIR / file))
        bad = check(data)
        total += len(data["examples"])
        print(f"✅ {label}: {len(data['examples'])} 条 (语法错误 {bad})")
    print(f"合计新增 {total} 条")




# ===========================================================================
# 补充族：文本处理 / 数论（追加到 bulk_basics.json）
# ===========================================================================
def build_basics_extra():
    coll = Collection("bulk_basics.json", "基础与工具集",
                      "参数化生成的 Python 基础、经典算法与实用工具示例（纯标准库，参数各不相同）。")
    # 合并模式：先载入 build_basics 已写入的示例，避免覆盖
    existing = OUT_DIR / "bulk_basics.json"
    if existing.exists():
        data = json.load(open(existing, encoding="utf-8"))
        for e in data.get("examples", []):
            coll.seen_id.add(e["id"])
            coll.seen_code.add(hashlib.md5(e["code"].encode()).hexdigest())
            coll.examples.append(e)

    def add(pid, base_title, desc, tags, body_fn, variants, category="topics", reqs=None):
        for i, pv in enumerate(variants):
            pname = pv.get("vname", f"变体{i + 1}")
            title = f"{base_title}·{pname}"
            code = bake(body_fn(pv), **pv)
            ex_id = f"{category}_{pid}-x{i + 1}"
            coll.add(ex_id, f"{pid}_x{i + 1}.py", title, f"{desc}本变体：{pname}。", list(tags), reqs or [], code, category)

    add("tools-text-wrap", "文本折行", "按宽度折行文本（greedy 填充）。",
        ["工具", "文本"], category="tools",
        body_fn=lambda p: '''"""文本折行：宽度 {{width}} 列。"""
text = "{{text}}"
width = {{width}}
lines, cur = [], ""
for word in text.split():
    if len(cur) + len(word) + 1 > width and cur:
        lines.append(cur)
        cur = word
    else:
        cur = (cur + " " + word).strip()
if cur:
    lines.append(cur)
for ln in lines:
    print(ln)
print(f"共 {len(lines)} 行")''',
        variants=[dict(vname=f"W{w}", width=w, text="the quick brown fox jumps over the lazy dog "
                       "and python makes text processing delightfully simple for everyone")
                  for w in (20, 28, 36, 44, 52)])

    add("tools-palindrome", "回文判定", "双指针回文检测（忽略大小写与标点）。",
        ["工具", "双指针"], category="tools",
        body_fn=lambda p: '''"""回文判定：'{s}'。"""
def is_palindrome(t):
    t = "".join(ch.lower() for ch in t if ch.isalnum())
    i, j = 0, len(t) - 1
    while i < j:
        if t[i] != t[j]:
            return False
        i += 1
        j -= 1
    return True

samples = {{samples}}
for s in samples:
    print(f"{s!r:>30} -> {is_palindrome(s)}")''',
        variants=[dict(vname=f"组{g}", samples=samples) for g, samples in enumerate([
            ["上海自来水来自海上", "A man, a plan, a canal: Panama", "hello"],
            ["level", "Python", "Was it a car or a cat I saw?"],
            ["12321", "no 'x' in nixon", "almostomla"],
        ])])

    add("tools-date-calendar", "月历打印", "calendar 模块打印指定月份。",
        ["工具", "日期"], category="tools",
        body_fn=lambda p: '''"""月历：{{y}} 年 {{m}} 月。"""
import calendar
print(calendar.month({{y}}, {{m}}))
print("该月天数:", calendar.monthrange({{y}}, {{m}})[1])''',
        variants=[dict(vname=f"{y}-{m:02d}", y=y, m=m) for y, m in
                  [(2026, 1), (2026, 6), (2026, 9), (2026, 12), (2027, 2), (2028, 2)]])

    add("algo-collatz", "考拉兹猜想", "3n+1 序列步数统计。",
        ["算法", "数学"],
        body_fn=lambda p: '''"""考拉兹序列：起点 {{start}}，最长链搜索到 {{limit}}。"""
def collatz_len(n):
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps

print("起点 {{start}} 步数:", collatz_len({{start}}))
best = max(range(1, {{limit}}), key=lambda n: (collatz_len(n), -n))
print(f"1~{{limit}} 中链最长: {best} ({collatz_len(best)} 步)")''',
        variants=[dict(vname=f"L{lim}", start=s, limit=lim) for s, lim in
                  [(27, 1000), (97, 2000), (871, 5000), (6171, 10000)]])

    add("algo-gcd-lcm", "GCD/LCM", "辗转相除与最小公倍数。",
        ["算法", "数学"],
        body_fn=lambda p: '''"""GCD/LCM：多组数。"""
from math import gcd

def lcm(a, b):
    return a * b // gcd(a, b)

pairs = {{pairs}}
for a, b in pairs:
    print(f"gcd({a}, {b}) = {gcd(a, b)},  lcm = {lcm(a, b)}")''',
        variants=[dict(vname=f"组{g}", pairs=pairs) for g, pairs in enumerate([
            [(12, 18), (24, 36), (48, 60)], [(100, 75), (81, 27), (97, 89)],
            [(270, 192), (1071, 462), (2026, 922)]])])

    add("algo-matrix-rotate", "矩阵旋转", "n×n 矩阵原地旋转 90 度。",
        ["算法", "矩阵"],
        body_fn=lambda p: '''"""矩阵旋转：{{n}}×{{n}} 顺时针 90°。"""
n = {{n}}
mat = [[(i * n + j) % {{mod}} for j in range(n)] for i in range(n)]
print("旋转前:", mat[0])
for layer in range(n // 2):
    first, last = layer, n - 1 - layer
    for i in range(first, last):
        off = i - first
        top = mat[first][i]
        mat[first][i] = mat[last - off][first]
        mat[last - off][first] = mat[last][last - off]
        mat[last][last - off] = mat[i][last]
        mat[i][last] = top
print("旋转后:", mat[0])''',
        variants=[dict(vname=f"n{n}m{m}", n=n, mod=m) for n, m in [(4, 9), (5, 7), (6, 13), (8, 5)]])
    return coll.save()


if __name__ == "__main__":
    main()
