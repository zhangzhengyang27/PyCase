"""波场线条·经典·v1
Turtle 绘图示例。多条相位渐移的正弦波线组成波场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for line_i in range(10):
    t.pencolor(colors[line_i % len(colors)])
    for x in range(-220, 220, 4):
        yv = 24 * math.sin(x * 0.02 + line_i * 0.3)
        t.goto(x, yv + line_i * 9 - 10 * 9 / 2)
        t.pendown() if x == -220 else None
t.hideturtle()
turtle.done()
