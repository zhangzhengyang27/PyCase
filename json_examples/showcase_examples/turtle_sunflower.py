"""{title}
Turtle 图形：{desc}
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

import math

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
