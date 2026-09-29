"""波场线条·樱粉·v7
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for line_i in range(22):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-280, 280, 4):
        yv = 42 * math.sin(x * 0.044 + line_i * 0.78)
        t.goto(x, yv + line_i * 15 - 22 * 15 / 2)
        t.pendown() if x == -280 else None
t.hideturtle()
turtle.done()
