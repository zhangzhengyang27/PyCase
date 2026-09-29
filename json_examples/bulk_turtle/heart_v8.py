"""心形曲线·石墨·v8
Turtle 绘图示例。参数化心形曲线（16sin³t 系），填充着色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.pencolor('#868e96')
t.fillcolor('#f8f9fa')
t.penup()
first = True
for i in range(0, 480):
    tval = math.pi * 2 * i / 480
    x = 16 * math.sin(tval) ** 3 * 17
    y = (13 * math.cos(tval) - 5 * math.cos(2 * tval) - 2 * math.cos(3 * tval) - math.cos(4 * tval)) * 17
    if first:
        t.goto(x, y); t.pendown(); first = False
    else:
        t.goto(x, y)
t.hideturtle()
turtle.done()
