"""波场线条·暮色·v5
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for line_i in range(18):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-260, 260, 4):
        yv = 36 * math.sin(x * 0.036000000000000004 + line_i * 0.62)
        t.goto(x, yv + line_i * 13 - 18 * 13 / 2)
        t.pendown() if x == -260 else None
t.hideturtle()
turtle.done()
