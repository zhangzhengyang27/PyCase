#!/usr/bin/env python3
"""生成「新建示例集」showcase_examples.json。

2026-09-22 数据重建：原示例库（1187 条）随事故丢失，本脚本按五大主题
（Turtle 绘图 / Pygame 游戏 / OpenCV 视觉 / Python 基础 / 实用工具）重建
一批可直接运行、自包含、无网络的示例。PIL 与数据可视化两个主题由
gen_pil_examples.py / gen_dataviz_examples.py 覆盖，sciviz 待重建。
"""
import json
import os

EXAMPLES = []


def add(example_id, name, title, description, tags, requirements, code, category="topics"):
    EXAMPLES.append({
        "id": example_id,
        "name": name,
        "category": category,
        "tags": tags,
        "title": title,
        "description": description,
        "requirements": requirements,
        "code": code.strip() + "\n",
    })


# ============================================================ Python 基础
add("hello_world", "hello_world.py", "你好，世界",
    "最经典的入门示例：打印问候语，演示 print 与 f-string 基础。",
    ["基础", "入门"], [],
    '''
"""你好，世界 —— 每个程序员的第一个脚本。"""
name = "Python"
version = 3.12
print(f"Hello, {name} {version}!")
print("你好，世界！")

# 多行输出与简单运算
for i in range(1, 4):
    print(f"第 {i} 行：{i} x {i} = {i * i}")
''')

add("topics_basics_string-format", "string_format.py", "字符串格式化大全",
    "演示 %、format、f-string 三代格式化方式与对齐、填充、进制转换。",
    ["基础", "字符串"], [],
    '''
"""字符串格式化：三代语法对照。"""
pi = 3.14159265
name, score = "小明", 92.5

# 1) %-格式化（C 风格）
print("%s 的成绩是 %.1f" % (name, score))
# 2) str.format
print("{} 的成绩是 {:.2f}，百分比 {:.0%}".format(name, score, score / 100))
# 3) f-string（推荐）：表达式、对齐、填充、进制
print(f"{name:=^10} 的成绩 {score:*>8.2f}")
print(f"圆周率保留三位: {pi:.3f}，十六进制: {255:x}，二进制: {5:b}")
print(f"大数分隔: {1234567890:,}")

# 三引号多行模板
report = f"""
=== 成绩单 ===
姓名: {name}
成绩: {score}
等级: {'优秀' if score >= 90 else '良好'}
"""
print(report)
''')

add("topics_basics-comprehension", "comprehension.py", "列表/字典/集合推导式",
    "用推导式替换循环：过滤、映射、嵌套、条件表达式与生成器表达式。",
    ["基础", "推导式"], [],
    '''
"""推导式：Pythonic 数据变换的核心写法。"""
nums = range(1, 21)

# 列表推导：平方 + 过滤
squares = [n * n for n in nums if n % 2 == 0]
print("偶数的平方:", squares)

# 字典推导：单词 -> 长度
words = ["apple", "banana", "cherry", "avocado"]
lengths = {w: len(w) for w in words}
print("词长字典:", lengths)

# 集合推导：去重首字母
firsts = {w[0] for w in words}
print("首字母集合:", firsts)

# 嵌套推导：九九乘法表上三角
table = [(i, j, i * j) for i in range(1, 6) for j in range(i, 6)]
print("乘法组合数:", len(table))

# 生成器表达式：惰性求值省内存
total = sum(n * n for n in nums)
print("1~20 平方和:", total)
''')

add("topics_basics-decorator", "decorator.py", "装饰器：计时器与重试",
    "用 functools.wraps 实现函数计时器与失败重试装饰器，理解闭包与语法糖。",
    ["基础", "装饰器", "函数"], [],
    '''
"""装饰器实战：计时 + 重试。"""
import functools
import time
import random


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        cost = (time.perf_counter() - start) * 1000
        print(f"[timer] {func.__name__} 耗时 {cost:.2f}ms")
        return result
    return wrapper


def retry(times=3, delay=0.1):
    """失败自动重试的参数化装饰器。"""
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"[retry] 第 {attempt} 次失败: {e}")
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return deco


@timer
def slow_add(a, b):
    time.sleep(0.05)
    return a + b


@retry(times=4)
def flaky():
    """30% 概率失败，演示重试。"""
    if random.random() < 0.3:
        raise RuntimeError("随机故障")
    return "成功"


print(slow_add(1, 2))
print(flaky())
''')

add("topics_basics-generator", "generator.py", "生成器与 yield",
    "用生成器惰性产出斐波那契与素数，演示 yield、send 与内存优势。",
    ["基础", "生成器", "迭代"], [],
    '''
"""生成器：惰性序列。"""
import itertools


def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def primes(limit):
    """埃拉托斯特尼筛法的生成器版本。"""
    sieve = [True] * (limit + 1)
    for n in range(2, limit + 1):
        if sieve[n]:
            yield n
            for m in range(n * n, limit + 1, n):
                sieve[m] = False


# 取前 10 个斐波那契数（无限序列只按需计算）
fib = itertools.islice(fibonacci(), 10)
print("斐波那契:", list(fib))

print("100 以内素数:", list(primes(100)))

# 生成器表达式与 sum/all 组合
squares = (n * n for n in range(10))
print("平方和:", sum(squares))
print("全为正:", all(x > 0 for x in [1, 2, 3]))
''')

add("topics_basics-dataclass", "dataclass_demo.py", "dataclass 数据类",
    "用 @dataclass 声明不可变记录与默认排序，对比手写 __init__ 的样板代码。",
    ["基础", "OOP", "dataclass"], [],
    '''
"""dataclass：声明式数据模型。"""
from dataclasses import dataclass, field


@dataclass(order=True, frozen=True)
class Student:
    sort_index: float = field(init=False, repr=False)
    name: str
    score: float

    def __post_init__(self):
        object.__setattr__(self, "sort_index", -self.score)  # 分数降序


students = [
    Student("小明", 92.5),
    Student("小红", 88.0),
    Student("小刚", 95.0),
]
for rank, s in enumerate(sorted(students), 1):
    print(f"第{rank}名 {s.name} {s.score}")

# frozen=True 不可变：修改会抛 FrozenInstanceError
try:
    students[0].score = 0
except Exception as e:
    print("不可变校验:", type(e).__name__)
''')

add("topics_basics-pathlib", "pathlib_demo.py", "pathlib 文件操作",
    "用 pathlib 完成遍历、过滤、读写、重命名与临时目录操作，替代 os.path 拼接。",
    ["基础", "文件", "pathlib"], [],
    '''
"""pathlib：现代文件路径操作。"""
from pathlib import Path
import tempfile

base = Path(tempfile.mkdtemp(prefix="pathlib_demo_"))
(base / "docs").mkdir()
(base / "logs").mkdir()
(base / "docs" / "a.txt").write_text("hello", encoding="utf-8")
(base / "docs" / "b.md").write_text("# hi", encoding="utf-8")
(base / "logs" / "run.log").write_text("INFO ok", encoding="utf-8")

# glob 遍历
print("全部文件:", sorted(p.name for p in base.rglob("*") if p.is_file()))
print("markdown:", [p.name for p in base.rglob("*.md")])

# 读写与属性
doc = base / "docs" / "a.txt"
print("内容:", doc.read_text(encoding="utf-8"), "| 大小:", doc.stat().st_size)

# 重命名 + 目录树
doc.rename(doc.with_name("renamed.txt"))
for p in sorted(base.rglob("*")):
    print("  " * (len(p.relative_to(base).parts) - 1), p.name)
''')

add("topics_basics-regex", "regex_demo.py", "正则表达式实战",
    "用 re 完成提取邮箱/日期、分组替换与贪婪非贪婪，附常用模式速查。",
    ["基础", "正则", "re"], [],
    '''
"""正则表达式：提取、分组与替换。"""
import re

text = """
联系人: alice@example.com, 备用: bob.smith@mail.org
会议时间: 2026-09-22 14:30 ~ 2026-09-23 09:00
订单号: ORD-2026-0922-001, 金额: ￥1,299.00
"""

# 邮箱提取
emails = re.findall(r"[\\w.+-]+@[\\w-]+\\.[\\w.]+", text)
print("邮箱:", emails)

# 命名分组解析日期
for m in re.finditer(r"(?P<y>\\d{4})-(?P<m>\\d{2})-(?P<d>\\d{2})", text):
    print("日期:", m.groupdict())

# 分组替换：订单号脱敏
masked = re.sub(r"(ORD-\\d{4})-\\d{4}-(\\d+)", r"\\1-****-\\2", text)
print("脱敏:", masked.strip().splitlines()[-1])

# 贪婪 vs 非贪婪
print("贪婪:", re.findall(r"时间: .*?\\d", text)[0][:20])
''')

add("topics_basics-error-handling", "error_handling.py", "异常处理与自定义异常",
    "演示 try/except/else/finally、异常链与自定义业务异常的最佳实践。",
    ["基础", "异常"], [],
    '''
"""异常处理：分层捕获与自定义异常。"""
import json


class AppError(Exception):
    """业务异常基类。"""


class ConfigNotFound(AppError):
    pass


class BadConfigValue(AppError):
    pass


def load_config(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigNotFound(f"配置解析失败: {e}") from e
    if "retries" not in data:
        raise BadConfigValue("缺少 retries 字段")
    if not isinstance(data["retries"], int):
        raise BadConfigValue("retries 必须是整数")
    return data


# 正常路径
print(load_config('{"retries": 3}'))

# 两种失败路径
for bad in ['{"name": "x"}', "not-json"]:
    try:
        load_config(bad)
    except ConfigNotFound as e:
        print("配置错误:", e)
    except BadConfigValue as e:
        print("字段错误:", e)
    finally:
        print("  (finally 总会执行)")
''')

# ============================================================ Turtle 绘图
turtle_head = '''"""{title}
Turtle 图形：{desc}
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

'''

def turtle_code(body):
    return turtle_head + body

add("topics_turtle-spiral", "turtle_spiral.py", "彩色螺旋线",
    "用循环改变边长与颜色绘制渐变螺旋，演示 turtle 基本循环绘图。",
    ["Turtle", "图形"], [],
    turtle_code('''t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("black")
colors = ["red", "orange", "yellow", "green", "cyan", "purple"]

for i in range(120):
    t.pencolor(colors[i % 6])
    t.width(i // 20 + 1)
    t.forward(i * 2)
    t.left(59)

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-rose", "turtle_rose.py", "数学玫瑰线",
    "参数方程 petals 瓣玫瑰线，体会极坐标与循环角度的对应关系。",
    ["Turtle", "数学"], [],
    turtle_code('''import math

t = turtle.Turtle()
t.speed(0)
t.pensize(2)
petals = 5

for i in range(361):
    rad = math.radians(i)
    r = 150 * math.sin(petals * rad)
    x, y = r * math.cos(rad), r * math.sin(rad)
    t.goto(x, y)

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-fractal-tree", "turtle_fractal_tree.py", "递归分形树",
    "递归绘制二叉分形树，随深度改变枝干粗细与颜色，理解递归图形。",
    ["Turtle", "递归", "分形"], [],
    turtle_code('''t = turtle.Turtle()
t.left(90)
t.speed(0)


def tree(length: float, depth: int):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor("brown" if depth > 3 else "green")
    t.forward(length)
    t.left(25)
    tree(length * 0.72, depth - 1)
    t.right(50)
    tree(length * 0.72, depth - 1)
    t.left(25)
    t.backward(length)


tree(90, 8)
t.hideturtle()
turtle.done()
'''))

add("topics_turtle-koch", "turtle_koch_snowflake.py", "科赫雪花",
    "经典分形：三段科赫曲线组成雪花，观察迭代次数与复杂度的关系。",
    ["Turtle", "分形"], [],
    turtle_code('''t = turtle.Turtle()
t.speed(0)
t.pensize(2)
t.pencolor("#1e6fd9")


def koch(length: float, depth: int):
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
    koch(240, 3)
    t.right(120)

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-rainbow-circles", "turtle_rainbow_circles.py", "彩虹同心圆",
    "HSV 颜色空间渐变填充同心圆，演示 colorsys 与 begin_fill/end_fill。",
    ["Turtle", "颜色"], [],
    turtle_code('''import colorsys

t = turtle.Turtle()
t.speed(0)
t.penup()

for i in range(36):
    r, g, b = colorsys.hsv_to_rgb(i / 36, 0.9, 1.0)
    t.pencolor(r, g, b)
    t.fillcolor(r, g, b)
    t.sety(-i * 4)
    t.pendown()
    t.begin_fill()
    t.circle(20 + i * 4)
    t.end_fill()
    t.penup()

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-starfield", "turtle_starfield.py", "随机星空",
    "随机位置与大小绘制五角星，练习 random 与封装的 draw_star 函数。",
    ["Turtle", "随机"], [],
    turtle_code('''import random

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("#0b1026")
t.penup()


def draw_star(x, y, size, color):
    t.penup()
    t.goto(x, y)
    t.setheading(random.randint(0, 360))
    t.pendown()
    t.pencolor(color)
    t.fillcolor(color)
    t.begin_fill()
    for _ in range(5):
        t.forward(size)
        t.right(144)
    t.end_fill()


palette = ["#ffd76e", "#ffffff", "#9fd8ff", "#ffb3c6"]
for _ in range(40):
    draw_star(random.randint(-280, 280), random.randint(-220, 220),
              random.randint(6, 18), random.choice(palette))

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-kaleidoscope", "turtle_kaleidoscope.py", "万花筒",
    "外层旋转复制内层花纹，两层循环构成对称图案，体会坐标变换叠加。",
    ["Turtle", "图案"], [],
    turtle_code('''t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("black")
colors = ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#f368e0"]


def petal():
    for _ in range(6):
        t.forward(60)
        t.right(60)
    t.forward(30)


for ring in range(6):
    t.pencolor(colors[ring % 5])
    for _ in range(12):
        petal()
        t.right(30)
    t.right(10)
    t.forward(8)

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-maze-walk", "turtle_maze_walk.py", "随机游走轨迹",
    "带边界反弹的随机游走并留下渐变轨迹，演示状态机式循环与取模变色。",
    ["Turtle", "随机"], [],
    turtle_code('''import random

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("#101418")
t.penup()
t.goto(0, 0)
t.pendown()

steps = 300
for i in range(steps):
    t.pencolor((i / steps, 1 - i / steps, 0.5 + 0.5 * (i % 20 < 10)))
    t.setheading(random.choice([0, 90, 180, 270]))
    t.forward(12)
    x, y = t.position()
    if abs(x) > 280 or abs(y) > 220:  # 越界回中
        t.penup()
        t.goto(0, 0)
        t.pendown()

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-sunflower", "turtle_sunflower.py", "向日葵花盘",
    "按黄金角 137.5 度排布种子点，用斐波那契螺线模拟真实向日葵排布。",
    ["Turtle", "数学", "自然"], [],
    turtle_code('''import math

t = turtle.Turtle()
t.speed(0)
t.penup()
turtle.bgcolor("#22251f")

GOLDEN_ANGLE = 137.507764
for i in range(400):
    r = 4.2 * math.sqrt(i)
    theta = i * GOLDEN_ANGLE
    x, y = r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta))
    t.goto(x, y)
    size = 2 + i / 60
    ratio = i / 400
    t.pencolor(0.9, 0.75 - 0.4 * ratio, 0.1)
    t.dot(size)

t.hideturtle()
turtle.done()
'''))

add("topics_turtle-city-skyline", "turtle_city_skyline.py", "像素城市天际线",
    "随机楼层拼贴城市剪影并点亮点亮窗口，练习矩形填充与分层构图。",
    ["Turtle", "图案", "随机"], [],
    turtle_code('''import random

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("#0d1b2a")
t.penup()

x = -300
while x < 300:
    width = random.randint(30, 60)
    height = random.randint(60, 180)
    t.goto(x, -180)
    t.pencolor("#1b263b")
    t.fillcolor("#1b263b")
    t.setheading(0)
    t.pendown()
    t.begin_fill()
    for side, dist in [(90, height), (0, width), (-90, height), (180, width)]:
        t.setheading(side)
        t.forward(dist)
    t.end_fill()
    # 亮窗
    for _ in range(random.randint(3, 8)):
        wx = x + random.randint(6, width - 10)
        wy = -180 + random.randint(10, height - 12)
        t.penup()
        t.goto(wx, wy)
        t.dot(3, "#ffd166")
    x += width + 6

t.hideturtle()
turtle.done()
'''))

# ============================================================ Pygame 游戏
pygame_note = "运行后弹出游戏窗口，按窗口关闭键或 ESC 退出。"

add("topics_pygame-snake", "pygame_snake.py", "贪吃蛇",
    "方向键控制贪吃蛇吃食物变长，撞墙或咬到自己结束，网格逻辑 + 事件循环入门。",
    ["Pygame", "游戏"], ["pygame"],
    f'''"""贪吃蛇：网格移动 + 事件循环。{pygame_note}"""
import random
import sys

import pygame

CELL, COLS, ROWS = 24, 26, 20
pygame.init()
screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("贪吃蛇")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

snake = [(COLS // 2, ROWS // 2)]
direction = (1, 0)
food = (random.randrange(COLS), random.randrange(ROWS))
score = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            turn = {{pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
                     pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}}.get(event.key)
            if turn and (turn[0] != -direction[0] or turn[1] != -direction[1]):
                direction = turn

    head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    if (head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS
            or head in snake):
        print(f"游戏结束，得分 {{score}}")
        break
    snake.insert(0, head)
    if head == food:
        score += 1
        food = (random.randrange(COLS), random.randrange(ROWS))
    else:
        snake.pop()

    screen.fill((18, 18, 24))
    for x, y in snake:
        pygame.draw.rect(screen, (80, 220, 120), (x * CELL, y * CELL, CELL - 2, CELL - 2), border_radius=4)
    pygame.draw.rect(screen, (230, 90, 90), (food[0] * CELL, food[1] * CELL, CELL - 2, CELL - 2), border_radius=8)
    screen.blit(font.render(f"Score: {{score}}", True, (240, 240, 240)), (8, 6))
    pygame.display.flip()
    clock.tick(8)
''')

add("topics_pygame-pong", "pygame_pong.py", "双人弹球对战",
    "W/S 与方向键分别控制两侧球拍，先得 5 分者胜，演示碰撞反弹与双输入。",
    ["Pygame", "游戏"], ["pygame"],
    f'''"""Pong：双人弹球。{pygame_note}"""
import sys

import pygame

W, H = 720, 440
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pong")
clock = pygame.font.Clock if False else pygame.time.Clock()
font = pygame.font.SysFont(None, 32)

paddle_h, speed = 84, 6
left = pygame.Rect(16, H // 2 - paddle_h // 2, 12, paddle_h)
right = pygame.Rect(W - 28, H // 2 - paddle_h // 2, 12, paddle_h)
ball = pygame.Rect(W // 2 - 6, H // 2 - 6, 12, 12)
ball_v = [4.2, 3.1]
score = [0, 0]

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        left.y -= speed
    if keys[pygame.K_s]:
        left.y += speed
    if keys[pygame.K_UP]:
        right.y -= speed
    if keys[pygame.K_DOWN]:
        right.y += speed
    left.clamp_ip((0, 0, W, H))
    right.clamp_ip((0, 0, W, H))

    ball.x += int(ball_v[0])
    ball.y += int(ball_v[1])
    if ball.top <= 0 or ball.bottom >= H:
        ball_v[1] *= -1
    if ball.colliderect(left) or ball.colliderect(right):
        ball_v[0] *= -1.05
    if ball.left <= 0:
        score[1] += 1
        ball.center = (W // 2, H // 2)
    if ball.right >= W:
        score[0] += 1
        ball.center = (W // 2, H // 2)

    screen.fill((16, 20, 28))
    pygame.draw.rect(screen, (240, 240, 240), left)
    pygame.draw.rect(screen, (240, 240, 240), right)
    pygame.draw.rect(screen, (255, 200, 80), ball)
    screen.blit(font.render(f"{{score[0]}} : {{score[1]}}", True, (240, 240, 240)), (W // 2 - 40, 10))
    pygame.display.flip()
    clock.tick(60)
    if 5 in score:
        print(f"比赛结束 {{score[0]}}:{{score[1]}}")
        break
''')

add("topics_pygame-catch", "pygame_catch_fruit.py", "接水果",
    "左右移动篮子接住下落水果，漏接扣命，随机生成 + AABB 碰撞入门。",
    ["Pygame", "游戏"], ["pygame"],
    f'''"""接水果：移动与碰撞。{pygame_note}"""
import random
import sys

import pygame

W, H = 560, 480
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("接水果")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

basket = pygame.Rect(W // 2 - 44, H - 60, 88, 26)
fruits = []
lives, caught, spawn_ms = 3, 0, 0

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        basket.x -= 7
    if keys[pygame.K_RIGHT]:
        basket.x += 7
    basket.clamp_ip((0, 0, W, basket.height))

    spawn_ms += dt
    if spawn_ms > 520:
        spawn_ms = 0
        fruits.append(pygame.Rect(random.randint(0, W - 22), -22, 22, 22))

    for f in fruits[:]:
        f.y += 4
        if f.colliderect(basket):
            fruits.remove(f)
            caught += 1
        elif f.y > H:
            fruits.remove(f)
            lives -= 1

    screen.fill((24, 28, 36))
    pygame.draw.rect(screen, (120, 200, 250), basket, border_radius=6)
    for f in fruits:
        pygame.draw.circle(screen, (240, 120, 120), f.center, 11)
    screen.blit(font.render(f"接住 {{caught}}  生命 {{lives}}", True, (240, 240, 240)), (10, 8))
    pygame.display.flip()
    if lives <= 0:
        print(f"游戏结束，接住 {{caught}} 个")
        break
''')

add("topics_pygame-breakout", "pygame_breakout.py", "打砖块",
    "挡板反弹消除整排砖块，砖块阵生成 + 多目标碰撞 + 胜负判定。",
    ["Pygame", "游戏"], ["pygame"],
    f'''"""打砖块 Breakout。{pygame_note}"""
import sys

import pygame

W, H = 560, 480
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("打砖块")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

paddle = pygame.Rect(W // 2 - 40, H - 40, 80, 12)
ball = pygame.Rect(W // 2 - 6, H // 2, 12, 12)
ball_v = [3.6, -3.8]

bricks = []
for row in range(5):
    for col in range(9):
        bricks.append(pygame.Rect(24 + col * 58, 50 + row * 26, 52, 20))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        paddle.x -= 6
    if keys[pygame.K_RIGHT]:
        paddle.x += 6
    paddle.clamp_ip((0, 0, W, H))

    ball.x += int(ball_v[0])
    ball.y += int(ball_v[1])
    if ball.left <= 0 or ball.right >= W:
        ball_v[0] *= -1
    if ball.top <= 0:
        ball_v[1] *= -1
    if ball.colliderect(paddle) and ball_v[1] > 0:
        ball_v[1] *= -1
    for b in bricks[:]:
        if ball.colliderect(b):
            bricks.remove(b)
            ball_v[1] *= -1
            break

    screen.fill((20, 22, 30))
    colors = [(230, 90, 90), (240, 160, 70), (250, 210, 90), (120, 210, 130), (110, 170, 250)]
    for i, b in enumerate(bricks):
        pygame.draw.rect(screen, colors[i // 9], b, border_radius=4)
    pygame.draw.rect(screen, (240, 240, 240), paddle, border_radius=6)
    pygame.draw.circle(screen, (255, 210, 120), ball.center, 6)
    pygame.display.flip()
    clock.tick(60)

    if not bricks:
        print("全部消除，你赢了！")
        break
    if ball.top > H:
        print("球落底，游戏结束")
        break
''')

add("topics_pygame-memory", "pygame_memory.py", "记忆翻牌",
    "4x4 翻牌配对游戏，用数字代替图案，演示状态机（翻开/比较/回退）。",
    ["Pygame", "游戏"], ["pygame"],
    f'''"""记忆翻牌：状态机小游戏。{pygame_note}"""
import random
import sys

import pygame

COLS, ROWS = 4, 4
CELL = 92
pygame.init()
screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("记忆翻牌")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 52)

deck = list(range(1, 9)) * 2
random.shuffle(deck)
cards = {{"value": deck, "open": [False] * 16, "matched": [False] * 16}}
first_pick = None

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            idx = pos[1] // CELL * COLS + pos[0] // CELL
            o, m = cards["open"], cards["matched"]
            if not o[idx] and not m[idx] and first_pick is None:
                o[idx] = True
                first_pick = idx
            elif not o[idx] and not m[idx] and first_pick is not None:
                o[idx] = True
                if cards["value"][idx] == cards["value"][first_pick]:
                    m[idx] = m[first_pick] = True
                first_pick = None

    screen.fill((30, 34, 44))
    for i in range(16):
        rect = pygame.Rect(i % COLS * CELL + 6, i // COLS * CELL + 6, CELL - 12, CELL - 12)
        if cards["open"][i] or cards["matched"][i]:
            pygame.draw.rect(screen, (70, 110, 90) if cards["matched"][i] else (90, 130, 200), rect, border_radius=8)
            img = font.render(str(cards["value"][i]), True, (245, 245, 245))
            screen.blit(img, img.get_rect(center=rect.center))
        else:
            pygame.draw.rect(screen, (60, 64, 78), rect, border_radius=8)
    pygame.display.flip()
    clock.tick(30)

    if all(cards["matched"]):
        print("全部配对完成！")
        break
''')

# ============================================================ OpenCV 视觉
cv_head = '''"""{title}
OpenCV 图像处理：{desc}
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np

'''

add("topics_opencv-edge", "opencv_edge_detect.py", "Canny 边缘检测",
    "合成场景图上对比 Sobel 与 Canny 两种边缘提取效果。",
    ["OpenCV", "边缘检测"], ["opencv-python", "numpy"],
    cv_head.format(title="Canny 边缘检测", desc="梯度与双阈值边缘提取。")
    + '''
img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)
cv2.GaussianBlur(img, (5, 5), 0, dst=img)

sobel = cv2.Sobel(img, cv2.CV_64F, 1, 1, ksize=3)
sobel = np.clip(np.abs(sobel), 0, 255).astype(np.uint8)
canny = cv2.Canny(img, 60, 150)

cv2.imshow("original", img)
cv2.imshow("sobel", sobel)
cv2.imshow("canny", canny)
cv2.waitKey(0)
cv2.destroyAllWindows()
''')

add("topics_opencv-colorspace", "opencv_colorspace.py", "颜色空间与通道",
    "BGR/HSV/灰度互转，并按 HSV 阈值提取红色物体掩膜。",
    ["OpenCV", "颜色"], ["opencv-python", "numpy"],
    cv_head.format(title="颜色空间", desc="HSV 阈值分割红色区域。")
    + '''
canvas = np.zeros((320, 480, 3), dtype=np.uint8)
cv2.circle(canvas, (120, 160), 70, (60, 60, 230), -1)     # 红色圆
cv2.rectangle(canvas, (260, 90), (420, 230), (90, 200, 90), -1)  # 绿色方块

hsv = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)

# HSV 中红色的两段阈值
mask1 = cv2.inRange(hsv, (0, 120, 120), (8, 255, 255))
mask2 = cv2.inRange(hsv, (170, 120, 120), (180, 255, 255))
red_mask = cv2.bitwise_or(mask1, mask2)
red_only = cv2.bitwise_and(canvas, canvas, mask=red_mask)

cv2.imshow("original", canvas)
cv2.imshow("gray", gray)
cv2.imshow("red_mask", red_mask)
cv2.imshow("red_only", red_only)
cv2.waitKey(0)
cv2.destroyAllWindows()
''')

add("topics_opencv-geometric", "opencv_geometric.py", "几何变换",
    "平移、旋转、缩放与仿射变换，理解变换矩阵与插值参数。",
    ["OpenCV", "几何"], ["opencv-python", "numpy"],
    cv_head.format(title="几何变换", desc="warpAffine 变换矩阵。")
    + '''
img = np.zeros((360, 480, 3), dtype=np.uint8)
cv2.putText(img, "CV", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 5, (180, 220, 255), 14)

rows, cols = img.shape[:2]
M_shift = np.float32([[1, 0, 60], [0, 1, 30]])
shifted = cv2.warpAffine(img, M_shift, (cols, rows))

M_rot = cv2.getRotationMatrix2D((cols / 2, rows / 2), 30, 0.8)
rotated = cv2.warpAffine(img, M_rot, (cols, rows))

resized = cv2.resize(img, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)

cv2.imshow("shifted", shifted)
cv2.imshow("rotated", rotated)
cv2.imshow("resized", resized)
cv2.waitKey(0)
cv2.destroyAllWindows()
''')

add("topics_opencv-threshold", "opencv_threshold.py", "阈值分割与自适应",
    "全局 Otsu 与自适应阈值对比，光照不均场景的分割选择。",
    ["OpenCV", "分割"], ["opencv-python", "numpy"],
    cv_head.format(title="阈值分割", desc="Otsu 与自适应阈值。")
    + '''
# 合成光照不均的渐变背景 + 字符
img = np.zeros((300, 480), dtype=np.uint8)
grad = np.linspace(40, 200, 480, dtype=np.uint8)[None, :]
img[:] = grad
cv2.putText(img, "THRESHOLD", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 2.2, 255, 10)
noise = np.random.randint(0, 12, img.shape, dtype=np.uint8)
img = cv2.add(img, noise)

_, otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
adaptive = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 25, 8)

cv2.imshow("original", img)
cv2.imshow("otsu", otsu)
cv2.imshow("adaptive", adaptive)
cv2.waitKey(0)
cv2.destroyAllWindows()
''')

add("topics_opencv-histogram", "opencv_histogram.py", "直方图均衡",
    "用均衡化增强低对比度图像，并用 calcHist 对比前后分布。",
    ["OpenCV", "增强"], ["opencv-python", "numpy"],
    cv_head.format(title="直方图均衡", desc="对比度增强。")
    + '''
# 低对比度图像
img = np.zeros((300, 480), dtype=np.uint8)
cv2.circle(img, (150, 150), 90, 110, -1)
cv2.rectangle(img, (280, 80), (420, 230), 150, -1)
img = (img * 0.35 + 60).astype(np.uint8)

equalized = cv2.equalizeHist(img)

hist_before = cv2.calcHist([img], [0], None, [256], [0, 256])
hist_after = cv2.calcHist([equalized], [0], None, [256], [0, 256])
print("原图标准差: %.1f -> 均衡后: %.1f" % (img.std(), equalized.std()))

cv2.imshow("before", img)
cv2.imshow("after", equalized)
cv2.waitKey(0)
cv2.destroyAllWindows()
''')

add("topics_opencv-contours", "opencv_contours.py", "轮廓检测与面积筛选",
    "findContours 提取轮廓，按面积过滤并标注质心，形状识别的基础流程。",
    ["OpenCV", "轮廓"], ["opencv-python", "numpy"],
    cv_head.format(title="轮廓检测", desc="面积过滤 + 质心标注。")
    + '''
img = np.zeros((360, 480), dtype=np.uint8)
cv2.circle(img, (110, 110), 62, 255, -1)
cv2.rectangle(img, (260, 60), (380, 180), 255, -1)
cv2.ellipse(img, (150, 280), (70, 34), 20, 0, 360, 255, -1)
cv2.circle(img, (360, 280), 18, 255, -1)

contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for c in contours:
    area = cv2.contourArea(c)
    if area < 800:  # 过滤小噪声
        continue
    M = cv2.moments(c)
    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
    cv2.drawContours(result, [c], -1, (80, 220, 120), 3)
    cv2.circle(result, (cx, cy), 4, (60, 90, 255), -1)
    cv2.putText(result, f"{int(area)}", (cx - 24, cy - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    print("轮廓面积:", int(area))

cv2.imshow("contours", result)
cv2.waitKey(0)
cv2.destroyAllWindows()
''')

# ============================================================ 实用工具脚本
add("tools_files-batch-rename", "batch_rename.py", "批量重命名工具",
    "按前缀 + 序号批量重命名目录内文件，dry-run 预览防止误操作。",
    ["工具", "文件"], [], 
    '''"""批量重命名：dry-run 预览 + 执行。"""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="目录内文件批量重命名")
    parser.add_argument("directory", nargs="?", default=".", help="目标目录")
    parser.add_argument("--prefix", default="file", help="新文件名前缀")
    parser.add_argument("--ext", default="", help="仅处理指定扩展名，如 .txt")
    parser.add_argument("--apply", action="store_true", help="真正执行（默认只预览）")
    args = parser.parse_args()

    target = Path(args.directory)
    files = sorted(p for p in target.iterdir()
                   if p.is_file() and (not args.ext or p.suffix == args.ext))
    plan = []
    for i, p in enumerate(files, 1):
        new_name = f"{args.prefix}_{i:03d}{p.suffix}"
        plan.append((p, p.with_name(new_name)))

    for old, new in plan:
        print(f"{old.name} -> {new.name}")
    if args.apply:
        for old, new in plan:
            old.rename(new)
        print(f"已重命名 {len(plan)} 个文件")
    else:
        print(f"（预览模式，共 {len(plan)} 个文件；加 --apply 执行）")


if __name__ == "__main__":
    main()
''', category="tools")

add("tools_csv-stats", "csv_stats.py", "CSV 列统计工具",
    "纯标准库解析 CSV 并输出数值列的计数/均值/最值，快速数据体检。",
    ["工具", "CSV", "数据"], [],
    '''"""CSV 数值列统计：纯标准库实现。"""
import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile", nargs="?", default="demo.csv")
    args = parser.parse_args()

    path = Path(args.csvfile)
    if not path.exists():
        path.write_text(
            "name,score,age\\n小明,92,14\\n小红,88,13\\n小刚,95,15\\n小丽,79,14\\n",
            encoding="utf-8",
        )

    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("空表格")
        return

    print(f"行数: {len(rows)}，列: {list(rows[0])}")
    for col in rows[0]:
        values = []
        for r in rows:
            try:
                values.append(float(r[col]))
            except ValueError:
                break
        if len(values) == len(rows):
            print(f"  [{col}] 计数={len(values)} 均值={sum(values)/len(values):.2f} "
                  f"最小={min(values)} 最大={max(values)}")


if __name__ == "__main__":
    main()
''', category="tools")

add("tools_log-analyzer", "log_analyzer.py", "日志等级统计",
    "解析日志行并统计各级别条数与错误明细，含正则解析与 Counter 应用。",
    ["工具", "日志", "正则"], [],
    '''''' + r'''"""日志分析：等级统计 + 错误明细。"""
import re
from collections import Counter

SAMPLE = """2026-09-22 10:00:01 INFO 服务启动 port=8000
2026-09-22 10:00:03 DEBUG 缓存预热 128 项
2026-09-22 10:01:22 WARN 响应超时 3.2s /api/list
2026-09-22 10:02:45 ERROR 数据库连接失败 retry=1
2026-09-22 10:03:10 INFO 请求 /health 200
2026-09-22 10:04:01 ERROR 数据库连接失败 retry=2
2026-09-22 10:05:33 WARN 慢查询 1.8s
"""

pattern = re.compile(r"^(?P<time>[\d-]+ [\d:]+) (?P<level>[A-Z]+) (?P<msg>.+)$")
counter = Counter()
errors = []

for line in SAMPLE.strip().splitlines():
    m = pattern.match(line)
    if not m:
        continue
    counter[m["level"]] += 1
    if m["level"] == "ERROR":
        errors.append((m["time"], m["msg"]))

print("等级分布:", dict(counter))
print("错误明细:")
for t, msg in errors:
    print(f"  {t}  {msg}")
''', category="tools")

add("tools_image-compress", "image_compress.py", "图片批量压缩",
    "用 Pillow 批量缩放并压缩目录内图片，保留比例与质量控制。",
    ["工具", "图片", "Pillow"], ["pillow"],
    '''"""图片批量压缩：等比缩放 + 质量控制。"""
import argparse
from pathlib import Path

from PIL import Image


def compress(path: Path, out: Path, max_side: int, quality: int) -> None:
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, max_side / max(w, h))
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        im.save(out, "JPEG", quality=quality, optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--max-side", type=int, default=1280)
    parser.add_argument("--quality", type=int, default=82)
    args = parser.parse_args()

    out_dir = Path(args.directory) / "compressed"
    out_dir.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).glob("*")):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"} or not p.is_file():
            continue
        out = out_dir / (p.stem + ".jpg")
        compress(p, out, args.max_side, args.quality)
        print(f"{p.name}: {p.stat().st_size // 1024}KB -> {out.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
''', category="tools")

add("tools_password-generator", "password_generator.py", "密码生成器",
    "按长度与字符集策略生成强密码，secrets 模块保证密码学安全随机。",
    ["工具", "安全"], [],
    '''"""密码生成器：secrets 安全随机。"""
import argparse
import secrets
import string


def generate(length: int, symbols: bool) -> str:
    pool = string.ascii_letters + string.digits
    if symbols:
        pool += "!@#$%^&*"
    while True:
        pwd = "".join(secrets.choice(pool) for _ in range(length))
        # 保证至少含小写、大写、数字
        if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                and any(c.isdigit() for c in pwd)):
            return pwd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=16, help="密码长度")
    parser.add_argument("--symbols", action="store_true", help="包含特殊符号")
    args = parser.parse_args()
    for _ in range(3):
        print(generate(args.n, args.symbols))


if __name__ == "__main__":
    main()
''', category="tools")

add("tools_timer-tomato", "tomato_timer.py", "命令行番茄钟",
    "25 分钟专注 + 5 分钟休息的终端计时器，演示 time 循环与跨平台响铃提示。",
    ["工具", "效率"], [],
    '''"""番茄钟：终端倒计时。"""
import argparse
import sys
import time


def countdown(minutes: int, label: str) -> None:
    total = minutes * 60
    for remain in range(total, 0, -1):
        mm, ss = divmod(remain, 60)
        sys.stdout.write(f"\\r{label} 剩余 {mm:02d}:{ss:02d} ")
        sys.stdout.flush()
        time.sleep(1)
    print(f"\\r{label} 完成！\\a")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus", type=int, default=1, help="专注时长(分钟)，演示用默认 1")
    parser.add_argument("--break-mins", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    for i in range(1, args.rounds + 1):
        print(f"—— 第 {i}/{args.rounds} 轮 ——")
        countdown(args.focus, "专注")
        if i < args.rounds:
            countdown(args.break_mins, "休息")


if __name__ == "__main__":
    main()
''', category="tools")

# 写出 JSON
out_path = os.path.join(os.path.dirname(__file__), "..", "json_examples", "showcase_examples.json")
out_path = os.path.normpath(out_path)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"name": "新建示例集", "description": "2026-09-22 数据重建：五大主题精选示例。",
               "examples": EXAMPLES}, f, ensure_ascii=False, indent=2)
print(f"✅ 已生成 {len(EXAMPLES)} 个新建示例 → {out_path}")
