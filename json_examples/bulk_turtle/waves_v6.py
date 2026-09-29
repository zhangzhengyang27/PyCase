"""波场线条·森绿·v6
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for line_i in range(20):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-270, 270, 4):
        yv = 39 * math.sin(x * 0.04 + line_i * 0.7)
        t.goto(x, yv + line_i * 14 - 20 * 14 / 2)
        t.pendown() if x == -270 else None
t.hideturtle()
turtle.done()
