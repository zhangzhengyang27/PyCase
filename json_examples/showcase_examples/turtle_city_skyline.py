"""像素城市天际线
Turtle 图形：随机楼层拼贴城市剪影并点亮点亮窗口，练习矩形填充与分层构图。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

import random

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
