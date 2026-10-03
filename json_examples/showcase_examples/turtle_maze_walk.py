"""随机游走轨迹
Turtle 图形：带边界反弹的随机游走并留下渐变轨迹，演示状态机式循环与取模变色。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

import random

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
