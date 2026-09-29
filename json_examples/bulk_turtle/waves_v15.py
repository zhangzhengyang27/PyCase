"""波场线条·樱粉·v15
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for line_i in range(38):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-360, 360, 4):
        yv = 66 * math.sin(x * 0.076 + line_i * 1.4200000000000002)
        t.goto(x, yv + line_i * 23 - 38 * 23 / 2)
        t.pendown() if x == -360 else None
t.hideturtle()
turtle.done()
