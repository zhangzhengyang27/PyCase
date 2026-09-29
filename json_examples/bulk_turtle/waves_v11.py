"""波场线条·暖阳·v11
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for line_i in range(30):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-320, 320, 4):
        yv = 54 * math.sin(x * 0.06 + line_i * 1.1)
        t.goto(x, yv + line_i * 19 - 30 * 19 / 2)
        t.pendown() if x == -320 else None
t.hideturtle()
turtle.done()
