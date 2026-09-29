"""波场线条·薄荷·v4
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for line_i in range(16):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-250, 250, 4):
        yv = 33 * math.sin(x * 0.032 + line_i * 0.54)
        t.goto(x, yv + line_i * 12 - 16 * 12 / 2)
        t.pendown() if x == -250 else None
t.hideturtle()
turtle.done()
