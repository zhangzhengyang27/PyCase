"""波场线条·薄荷·v12
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for line_i in range(32):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-330, 330, 4):
        yv = 57 * math.sin(x * 0.064 + line_i * 1.18)
        t.goto(x, yv + line_i * 20 - 32 * 20 / 2)
        t.pendown() if x == -330 else None
t.hideturtle()
turtle.done()
