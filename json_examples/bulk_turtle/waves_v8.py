"""波场线条·石墨·v8
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for line_i in range(24):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-290, 290, 4):
        yv = 45 * math.sin(x * 0.048 + line_i * 0.8600000000000001)
        t.goto(x, yv + line_i * 16 - 24 * 16 / 2)
        t.pendown() if x == -290 else None
t.hideturtle()
turtle.done()
