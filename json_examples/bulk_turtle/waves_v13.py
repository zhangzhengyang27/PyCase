"""波场线条·暮色·v13
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for line_i in range(34):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-340, 340, 4):
        yv = 60 * math.sin(x * 0.068 + line_i * 1.26)
        t.goto(x, yv + line_i * 21 - 34 * 21 / 2)
        t.pendown() if x == -340 else None
t.hideturtle()
turtle.done()
