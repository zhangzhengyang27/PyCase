"""波场线条·暖阳·v3
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for line_i in range(14):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-240, 240, 4):
        yv = 30 * math.sin(x * 0.028 + line_i * 0.45999999999999996)
        t.goto(x, yv + line_i * 11 - 14 * 11 / 2)
        t.pendown() if x == -240 else None
t.hideturtle()
turtle.done()
