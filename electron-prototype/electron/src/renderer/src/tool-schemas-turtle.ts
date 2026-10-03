// tool-schemas-turtle.ts：bulk_turtle 29 图形家族交互页（385 变体归并）。
// 迷你 turtle 引擎与 turtle 模块同构（forward/left/width/pencolor/goto/dot），
// 各族绘制循环忠实移植变体算法，落笔段用 matplotlib 渲染（sidecar 无头环境）。
// 变体的差异（角度/步长/深度/色板）全部变成页面参数。画廊路由专用注册。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const TURTLE_HEAD = `import json
import math
import random

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei", "Arial Unicode MS",
]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np

random.seed(42)

PALETTES = {
    "rainbow": ["#ffbe0b", "#fb5607", "#ff006e", "#8338ec", "#3a86ff"],
    "ocean": ["#023e8a", "#0077b6", "#00b4d8", "#48cae4", "#90e0ef"],
    "forest": ["#1b4332", "#2d6a4f", "#74c69d", "#95d5b2", "#d8f3dc"],
    "sunset": ["#f94144", "#f3722c", "#f8961e", "#fcbf49", "#f9c74f"],
    "mono": ["#22223b", "#4a4e69", "#9a8c98", "#c9ada7", "#f2e9e4"],
}
pal = PALETTES.get(palette, PALETTES["rainbow"])

class T:
    """迷你 turtle 引擎：与 turtle 模块同构的角度/前进语义，落笔段交 matplotlib。"""

    def __init__(self):
        self.x = self.y = 0.0
        self.h = 0.0
        self.segs = []
        self.dots = []
        self.cur = [(0.0, 0.0)]
        self.w = 1.0
        self.c = pal[0]

    def forward(self, d):
        nx = self.x + d * math.cos(math.radians(self.h))
        ny = self.y + d * math.sin(math.radians(self.h))
        self.cur.append((nx, ny))
        self.x, self.y = nx, ny

    def backward(self, d):
        self.forward(-d)

    def left(self, a):
        self.h += a

    def right(self, a):
        self.h -= a

    def width(self, w):
        self._flush()
        self.w = w

    def pencolor(self, c):
        self._flush()
        self.c = c

    def goto(self, x, y):
        self._flush()
        self.x, self.y = x, y
        self.cur = [(x, y)]

    def dot(self, r=3):
        self._flush()
        self.dots.append((self.x, self.y, r, self.c))

    def _flush(self):
        if len(self.cur) > 1:
            self.segs.append(([p[0] for p in self.cur], [p[1] for p in self.cur], self.w, self.c))
        self.cur = [(self.x, self.y)]

t = T()
`

const TURTLE_OUT = `t._flush()
fig, ax = plt.subplots(figsize=(7.5, 7.5))
for xs, ys, w, c in t.segs:
    ax.plot(xs, ys, linewidth=w, color=c, solid_capstyle="round")
if t.dots:
    ax.scatter([d[0] for d in t.dots], [d[1] for d in t.dots], s=[d[2] ** 2 for d in t.dots], c=[d[3] for d in t.dots], zorder=3)
ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout()
fig.savefig("turtle.png", dpi=150)
print("已输出 turtle.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "turtle.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

const PALETTE_FIELD = {
  key: 'palette',
  label: '色板',
  type: 'select' as const,
  default: 'rainbow',
  width: 'half' as const,
  options: [
    { value: 'rainbow', label: '霓虹彩虹' },
    { value: 'ocean', label: '深海蓝' },
    { value: 'forest', label: '森林绿' },
    { value: 'sunset', label: '落日橙' },
    { value: 'mono', label: '水墨灰' }
  ]
}

const P = (key: string, label: string, def: number, help?: string) => ({
  key, label, type: 'number' as const, default: def, width: 'half' as const, ...(help ? { help } : {})
})

export interface TurtleShape {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const turtleFamily = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): TurtleShape => ({ value, label, description, fields, body })


const N = (v: Record<string, unknown>, key: string, def: number, min = 1) =>
  Math.max(min, Math.trunc(Number(v[key]) || def))
const F = (v: Record<string, unknown>, key: string, def: number, min = 0.1) =>
  Math.max(min, Number(v[key]) || def)

export const TURTLE_SHAPES: TurtleShape[] = [
  turtleFamily('spiral', '渐变螺旋',
    '边长递增螺旋，色板取模轮换（bulk_turtle spiral 家族同款循环）。',
    [P('n', '段数', 140), P('angle', '转角', 61), P('step', '步长系数', 2.8)],
    (v) => `for i in range(${N(v, 'n', 140)}):
    t.pencolor(pal[i % len(pal)])
    t.width(1 + i // 17)
    t.forward(i * ${F(v, 'step', 2.8)})
    t.left(${F(v, 'angle', 61)})`),
  turtleFamily('spiral-square', '方螺旋',
    '直角递增螺旋（spiral-square 家族）。',
    [P('n', '段数', 120), P('angle', '转角', 91), P('step', '步长系数', 3)],
    (v) => `for i in range(${N(v, 'n', 120)}):
    t.pencolor(pal[i % len(pal)])
    t.width(1 + i // 20)
    t.forward(i * ${F(v, 'step', 3)})
    t.left(${F(v, 'angle', 91)})`),
  turtleFamily('rose', '多瓣玫瑰',
    '正多边形循环 + 整体旋转成花（rose 家族）。',
    [P('petals', '瓣数', 12), P('sides', '每瓣边数', 24), P('step', '边长', 12)],
    (v) => `petals, sides, step = ${N(v, 'petals', 12)}, ${N(v, 'sides', 24)}, ${F(v, 'step', 12)}
for k in range(petals):
    t.pencolor(pal[k % len(pal)])
    for _ in range(sides):
        t.forward(step)
        t.left(360 / sides)
    t.left(360 / petals)`),
  turtleFamily('fractal-tree', '分形树',
    '递归二叉分支（fractal-tree 家族）。',
    [P('depth', '递归深度', 9, '1~11'), P('len', '主干长', 110), P('angle', '分支角', 25)],
    (v) => `depth = min(11, ${N(v, 'depth', 9)})
def branch(length, d):
    if d == 0 or length < 2:
        return
    t.width(d * 0.9)
    t.pencolor(pal[min(len(pal) - 1, 4 - d // 3)])
    t.forward(length)
    t.left(${F(v, 'angle', 25)})
    branch(length * 0.72, d - 1)
    t.right(2 * ${F(v, 'angle', 25)})
    branch(length * 0.72, d - 1)
    t.left(${F(v, 'angle', 25)})
    t.backward(length)
t.left(90)
branch(${F(v, 'len', 110)}, depth)`),
  turtleFamily('koch', '科赫雪花',
    '三段科赫曲线闭合成雪花（koch 家族）。',
    [P('order', '阶数', 3, '0~4'), P('size', '边长', 280)],
    (v) => `order = min(4, ${N(v, 'order', 3)})
def koch(n, s):
    if n == 0:
        t.forward(s)
        return
    koch(n - 1, s / 3)
    t.left(60)
    koch(n - 1, s / 3)
    t.right(120)
    koch(n - 1, s / 3)
    t.left(60)
    koch(n - 1, s / 3)
t.width(1.6)
t.goto(-${F(v, 'size', 280)} / 2, ${F(v, 'size', 280)} / 3)
t.pencolor(pal[0])
for _ in range(3):
    koch(order, ${F(v, 'size', 280)})
    t.right(120)`),
  turtleFamily('sierpinski', '谢尔宾斯基三角',
    '递归三角形剖分（sierpinski 家族）。',
    [P('order', '阶数', 4, '0~5'), P('size', '边长', 300)],
    (v) => `order = min(5, ${N(v, 'order', 4)})
size = ${F(v, 'size', 300)}
def tri(x, y, s, d):
    if d == 0:
        t.width(1.2)
        t.pencolor(pal[min(len(pal) - 1, d + 1)])
        t.goto(x, y)
        for heading in (60, -120, -120):
            t.h = heading
            t.forward(s)
        return
    h = s * math.sqrt(3) / 4
    tri(x - s / 4, y - h / 2, s / 2, d - 1)
    tri(x + s / 4, y - h / 2, s / 2, d - 1)
    tri(x, y + h, s / 2, d - 1)
tri(0, -size * math.sqrt(3) / 6, size, order)`),
  turtleFamily('mandala', '曼陀罗',
    '图案单元绕心旋转（mandala 家族）。',
    [P('repeats', '重复份数', 18), P('sides', '单元边数', 8), P('step', '单元边长', 30)],
    (v) => `repeats, sides, step = ${N(v, 'repeats', 18)}, ${N(v, 'sides', 8)}, ${F(v, 'step', 30)}
for k in range(repeats):
    t.pencolor(pal[k % len(pal)])
    t.width(1 + k % 3)
    for _ in range(sides):
        t.forward(step)
        t.left(360 / sides + k * 0.5)
    t.left(360 / repeats)`),
  turtleFamily('lissajous', '利萨茹曲线',
    '参数方程逐段连线（lissajous 家族）。',
    [P('a', '频率 a', 3), P('b', '频率 b', 2), P('n', '采样段数', 600), P('phase', '相位°', 90)],
    (v) => `a, b, n = ${N(v, 'a', 3)}, ${N(v, 'b', 2)}, ${N(v, 'n', 600)}
phase = math.radians(${F(v, 'phase', 90)})
A, B = 220, 220
for i in range(n + 1):
    th = 2 * math.pi * i / n
    t.goto(A * math.sin(a * th + phase), B * math.sin(b * th))
t.pencolor(pal[2])
t.width(1.8)`),
  turtleFamily('phyllotaxis', '向日葵螺旋',
    '黄金角 137.5° 螺旋散点（phyllotaxis 家族）。',
    [P('n', '种子数', 350), P('spread', '扩散系数', 10)],
    (v) => `n = ${N(v, 'n', 350)}
spread = ${F(v, 'spread', 10)}
golden = 137.5
for i in range(n):
    r = spread * math.sqrt(i)
    t.h = i * golden
    t.goto(r * math.cos(math.radians(t.h)), r * math.sin(math.radians(t.h)))
    t.c = pal[i % len(pal)]
    t.dot(2 + i * 0.02)`),
  turtleFamily('polygon-ring', '多边形环',
    '逐环放大的多边形套叠（polygon-ring 家族）。',
    [P('rings', '环数', 24), P('sides', '边数', 6), P('step', '边长增量', 3)],
    (v) => `rings, sides = ${N(v, 'rings', 24)}, ${N(v, 'sides', 6)}
for k in range(rings):
    t.pencolor(pal[k % len(pal)])
    t.width(1 + k // 8)
    for _ in range(sides):
        t.forward(${F(v, 'step', 3)} * (k + 1))
        t.left(360 / sides)
    t.left(360 / rings * 0.5)`),
  turtleFamily('hex-flower', '六角花',
    '六边形绕心旋转叠加（hex-flower 家族）。',
    [P('petals', '份数', 12), P('size', '六边形边长', 45)],
    (v) => `petals, size = ${N(v, 'petals', 12)}, ${F(v, 'size', 45)}
for k in range(petals):
    t.pencolor(pal[k % len(pal)])
    t.width(1 + k % 2)
    for _ in range(6):
        t.forward(size)
        t.left(60)
    t.left(360 / petals)`),
  turtleFamily('butterfly', '蝴蝶曲线',
    '极坐标蝴蝶参数方程（butterfly 家族）。',
    [P('n', '采样段数', 900), P('scale', '尺寸系数', 150)],
    (v) => `n = ${N(v, 'n', 900)}
s = ${F(v, 'scale', 150)}
t.pencolor(pal[2])
t.width(1.6)
for i in range(n + 1):
    th = 12 * math.pi * i / n
    r = s * math.sin(th) * (math.e ** math.cos(th) - 2 * math.cos(4 * th) + math.sin(th / 12) ** 5)
    t.goto(r * math.sin(th), -r * math.cos(th))`),
  turtleFamily('galaxy', '星系旋臂',
    '对数螺旋散点星系（galaxy 家族）。',
    [P('n', '星点数', 400), P('arms', '旋臂数', 3)],
    (v) => `n, arms = ${N(v, 'n', 400)}, ${N(v, 'arms', 3)}
for i in range(n):
    arm = i % arms
    th = i * 0.035 + arm * 2 * math.pi / arms
    r = 4 * math.e ** (0.12 * th)
    t.goto(r * math.cos(th), r * math.sin(th))
    t.c = pal[i % len(pal)]
    t.dot(2 + random.random() * 4)`),
  turtleFamily('heart', '爱心曲线',
    '参数化心形（heart 家族）。',
    [P('n', '采样段数', 300), P('scale', '尺寸系数', 16)],
    (v) => `n = ${N(v, 'n', 300)}
s = ${F(v, 'scale', 16)}
t.pencolor(pal[2])
t.width(2.2)
for i in range(n + 1):
    th = 2 * math.pi * i / n
    t.goto(s * 16 * math.sin(th) ** 3, s * (13 * math.cos(th) - 5 * math.cos(2 * th) - 2 * math.cos(3 * th) - math.cos(4 * th)))`),
  turtleFamily('waves', '波纹',
    '多条相位错开的正弦波（waves 家族）。',
    [P('lines', '波线条数', 12), P('n', '每条采样', 200), P('amp', '振幅', 40)],
    (v) => `lines, n = ${N(v, 'lines', 12)}, ${N(v, 'n', 200)}
amp = ${F(v, 'amp', 40)}
for k in range(lines):
    t.pencolor(pal[k % len(pal)])
    t.width(1.4)
    t.goto(-320, -200 + k * 400 / lines)
    for i in range(n + 1):
        x = -320 + 640 * i / n
        t.goto(x, -200 + k * 400 / lines + amp * math.sin(2 * math.pi * i / n + k * 0.6))`),
  turtleFamily('rings', '同心环',
    '逐层放大的同心圆（rings 家族）。',
    [P('rings', '层数', 20), P('step', '半径增量', 15)],
    (v) => `rings = ${N(v, 'rings', 20)}
for k in range(rings):
    t.pencolor(pal[k % len(pal)])
    t.width(2 + k * 0.15)
    r = ${F(v, 'step', 15)} * (k + 1)
    t.goto(r, 0)
    t.h = 90
    for _ in range(90):
        t.forward(2 * r * math.pi / 90)
        t.left(4)`),
  turtleFamily('rays', '放射线',
    '过心射线均角旋转（rays 家族）。',
    [P('n', '射线数', 36), P('len', '线长', 300)],
    (v) => `n = ${N(v, 'n', 36)}
t.goto(0, 0)
for k in range(n):
    t.pencolor(pal[k % len(pal)])
    t.width(1.5 + k % 2)
    t.h = 360 * k / n
    t.forward(${F(v, 'len', 300)})
    t.goto(0, 0)`),
  turtleFamily('burst', '烟花绽放',
    '随机长度的放射线段（burst 家族）。',
    [P('n', '线段数', 80), P('len', '最大线长', 260)],
    (v) => `n = ${N(v, 'n', 80)}
for k in range(n):
    t.pencolor(pal[k % len(pal)])
    t.width(1 + random.random() * 2.5)
    t.h = 360 * k / n
    t.forward(${F(v, 'len', 260)} * (0.3 + random.random() * 0.7))
    t.goto(0, 0)`),
  turtleFamily('dot-field', '点阵场',
    '网格 + 抖动的彩色点场（dot-field 家族）。',
    [P('cols', '列数', 20), P('rows', '行数', 14), P('gap', '间距', 30)],
    (v) => `cols, rows, gap = ${N(v, 'cols', 20)}, ${N(v, 'rows', 14)}, ${F(v, 'gap', 30)}
for r in range(rows):
    for c in range(cols):
        x = (c - cols / 2) * gap + random.uniform(-3, 3)
        y = (r - rows / 2) * gap + random.uniform(-3, 3)
        t.goto(x, y)
        t.c = pal[(r + c) % len(pal)]
        t.dot(4 + 6 * math.sin((r + c) * 0.4) ** 2)`),
  turtleFamily('dragon', '龙形曲线',
    '折纸序列迭代生成（dragon 家族）。',
    [P('order', '阶数', 12, '1~16'), P('step', '段长', 9)],
    (v) => `order = min(16, ${N(v, 'order', 12)})
seq = "R"
for _ in range(order - 1):
    seq = seq + "R" + seq[::-1].translate(str.maketrans("LR", "RL"))
t.pencolor(pal[2])
t.width(1.4)
t.goto(-200, 100)
for ch in seq:
    t.forward(${F(v, 'step', 9)})
    t.right(90 if ch == "R" else -90)`),
  turtleFamily('square-stairs', '方阶梯',
    '逐级增大的方形阶梯（square-stairs 家族）。',
    [P('n', '阶数', 30), P('step', '阶宽', 9)],
    (v) => `n = ${N(v, 'n', 30)}
for k in range(n):
    t.pencolor(pal[k % len(pal)])
    t.width(1 + k // 10)
    for _ in range(2):
        t.forward(${F(v, 'step', 9)} * (k + 1))
        t.left(90)
    t.forward(${F(v, 'step', 9)} * (k + 1))
    t.right(90)`),
  turtleFamily('staircase-wave', '阶梯波',
    '阶梯高度按正弦调制（staircase-wave 家族）。',
    [P('n', '级数', 60), P('step', '级宽', 10), P('amp', '波幅', 120)],
    (v) => `n = ${N(v, 'n', 60)}
for k in range(n):
    t.pencolor(pal[k % len(pal)])
    t.h = 0
    t.forward(${F(v, 'step', 10)})
    rise = ${F(v, 'amp', 120)} * (math.sin(2 * math.pi * k / n) - math.sin(2 * math.pi * (k - 1) / n))
    t.h = 90
    t.forward(rise)`),
  turtleFamily('honeycomb', '蜂窝网格',
    '六边形平铺蜂巢（honeycomb 家族）。',
    [P('rings', '环数', 3, '1~6'), P('size', '边长', 30)],
    (v) => `rings = min(6, ${N(v, 'rings', 3)})
size = ${F(v, 'size', 30)}
def hex_at(x, y, c):
    t.goto(x, y)
    t.h = 0
    t.pencolor(c)
    for _ in range(6):
        t.forward(size)
        t.left(60)
t.width(1.4)
for q in range(-rings, rings + 1):
    for r in range(max(-rings, -q - rings), min(rings, -q + rings) + 1):
        cx = size * math.sqrt(3) * (q + r / 2)
        cy = size * 1.5 * r
        hex_at(cx, cy, pal[(q - r + 100) % len(pal)])`),
  turtleFamily('city-skyline', '城市天际线',
    '随机楼群矩形轮廓（city-skyline 单例）。',
    [P('buildings', '楼数', 14), P('max-h', '最高', 260), P('width', '楼宽', 60)],
    (v) => `n = ${N(v, 'buildings', 14)}
bw = ${F(v, 'width', 60)}
x = -n * bw / 2
for k in range(n):
    h = 60 + random.random() * ${F(v, 'max-h', 260)}
    t.pencolor(pal[k % len(pal)])
    t.width(2)
    t.goto(x, -200)
    t.h = 90
    t.forward(h)
    t.h = 0
    t.forward(bw)
    t.h = -90
    t.forward(h)
    x += bw`),
  turtleFamily('starfield', '星空',
    '随机散布的星点（starfield 单例）。',
    [P('n', '星数', 220), P('radius', '散布半径', 320)],
    (v) => `n = ${N(v, 'n', 220)}
for _ in range(n):
    t.goto(random.uniform(-320, 320), random.uniform(-320, 320))
    t.c = pal[int(random.random() * len(pal))]
    t.dot(2 + random.random() * 7)`),
  turtleFamily('kaleidoscope', '万花筒',
    '随机折线段多次镜像旋转（kaleidoscope 单例）。',
    [P('repeats', '镜像份数', 8), P('segs', '每份段数', 9), P('len', '段长', 60)],
    (v) => `repeats, segs = ${N(v, 'repeats', 8)}, ${N(v, 'segs', 9)}
base_segs = [(random.uniform(-1, 1) * ${F(v, 'len', 60)}, random.uniform(0, 360) / segs) for _ in range(segs)]
for k in range(repeats):
    t.pencolor(pal[k % len(pal)])
    t.width(1.6)
    t.goto(0, 0)
    t.h = 360 * k / repeats
    for dx, da in base_segs:
        t.forward(dx)
        t.left(da)
    t.goto(0, 0)`),
  turtleFamily('maze-walk', '迷宫游走',
    '随机直角转向的路径（maze-walk 单例）。',
    [P('n', '步数', 90), P('step', '步长', 28)],
    (v) => `n = ${N(v, 'n', 90)}
random.seed(7)
for k in range(n):
    t.pencolor(pal[k % len(pal)])
    t.width(2)
    t.forward(${F(v, 'step', 28)})
    t.right(random.choice([90, 90, 90, -90]))`),
  turtleFamily('rainbow-circles', '彩虹环',
    '色相渐变的同心圆（rainbow-circles 单例）。',
    [P('rings', '层数', 24), P('step', '半径增量', 13)],
    (v) => `rings = ${N(v, 'rings', 24)}
t.width(3)
for k in range(rings):
    hue = k / rings
    t.pencolor(f"#{int(255 * abs(math.sin(math.pi * hue * 3))):02x}{int(255 * hue):02x}{int(255 * (1 - hue)):02x}")
    r = ${F(v, 'step', 13)} * (k + 1)
    t.goto(r, 0)
    t.h = 90
    for _ in range(90):
        t.forward(2 * r * math.pi / 90)
        t.left(4)`),
  turtleFamily('sunflower', '太阳花',
    '花瓣旋转 + 花心密铺（sunflower 单例）。',
    [P('petals', '花瓣数', 16), P('size', '花瓣长', 70)],
    (v) => `petals = ${N(v, 'petals', 16)}
size = ${F(v, 'size', 70)}
for k in range(petals):
    t.pencolor(pal[k % len(pal)])
    t.width(2)
    for _ in range(2):
        for _ in range(8):
            t.forward(size / 8)
            t.left(360 / 8 / 2)
        t.left(360 / 8 * 3)
    t.left(360 / petals)
t.pencolor(pal[4])
for i in range(60):
    r = 4 * math.sqrt(i)
    t.h = i * 137.5
    t.goto(r * math.cos(math.radians(t.h)), r * math.sin(math.radians(t.h)))
    t.dot(3)`)
]

// ---------------------------------------------------------------------------
// turtle 图形画廊：29 图形家族归并单页
// ---------------------------------------------------------------------------
const TURTLE_SHAPE_FIELD: FieldSpec = {
  key: 'shape',
  label: '图形',
  type: 'select',
  default: 'spiral',
  width: 'full',
  options: TURTLE_SHAPES.map((t) => ({ value: t.value, label: t.label }))
}

export const turtleLabSchema: InteractiveToolSchema = {
  id: 'interactive:turtle-lab',
  title: 'turtle 图形画廊',
  description: 'bulk_turtle 29 图形家族的归并页：迷你 turtle 引擎忠实复刻变体绘制算法，选图形、调参数与色板。',
  tags: ['turtle', '绘图'],
  fields: (v) => {
    const t = TURTLE_SHAPES.find((x) => x.value === v.shape) ?? TURTLE_SHAPES[0]!
    return [TURTLE_SHAPE_FIELD, PALETTE_FIELD, ...t.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '图形', value: String(v.shape ?? 'spiral') }, { label: '色板', value: String(v.palette ?? 'rainbow') }] }),
  pyCode: (v) => {
    const t = TURTLE_SHAPES.find((x) => x.value === v.shape) ?? TURTLE_SHAPES[0]!
    return `palette = ${JSON.stringify(String(v.palette ?? 'rainbow'))}\n${TURTLE_HEAD}\n${t.body(v)}\n${TURTLE_OUT}`
  }
}
