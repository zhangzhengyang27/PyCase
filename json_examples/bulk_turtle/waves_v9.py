"""波场线条·经典·v9
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for line_i in range(26):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-300, 300, 4):
        yv = 48 * math.sin(x * 0.052000000000000005 + line_i * 0.94)
        t.goto(x, yv + line_i * 17 - 26 * 17 / 2)
        t.pendown() if x == -300 else None
t.hideturtle()
turtle.done()
