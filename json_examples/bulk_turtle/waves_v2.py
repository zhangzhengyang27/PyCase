"""波场线条·海雾·v2
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for line_i in range(12):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-230, 230, 4):
        yv = 27 * math.sin(x * 0.024 + line_i * 0.38)
        t.goto(x, yv + line_i * 10 - 12 * 10 / 2)
        t.pendown() if x == -230 else None
t.hideturtle()
turtle.done()
