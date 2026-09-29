"""波场线条·森绿·v14
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for line_i in range(36):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-350, 350, 4):
        yv = 63 * math.sin(x * 0.07200000000000001 + line_i * 1.34)
        t.goto(x, yv + line_i * 22 - 36 * 22 / 2)
        t.pendown() if x == -350 else None
t.hideturtle()
turtle.done()
