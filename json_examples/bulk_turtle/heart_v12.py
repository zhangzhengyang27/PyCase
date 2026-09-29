"""心形曲线·薄荷·v12
Turtle 绘图示例。参数化心形曲线（16sin³t 系），填充着色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(4)
t.pencolor('#72efdd')
t.fillcolor('#48bfe3')
t.penup()
first = True
for i in range(0, 640):
    tval = math.pi * 2 * i / 640
    x = 16 * math.sin(tval) ** 3 * 21
    y = (13 * math.cos(tval) - 5 * math.cos(2 * tval) - 2 * math.cos(3 * tval) - math.cos(4 * tval)) * 21
    if first:
        t.goto(x, y); t.pendown(); first = False
    else:
        t.goto(x, y)
t.hideturtle()
turtle.done()
