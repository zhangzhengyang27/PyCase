"""波场线条·海雾·v10
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for line_i in range(28):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-310, 310, 4):
        yv = 51 * math.sin(x * 0.05600000000000001 + line_i * 1.02)
        t.goto(x, yv + line_i * 18 - 28 * 18 / 2)
        t.pendown() if x == -310 else None
t.hideturtle()
turtle.done()
