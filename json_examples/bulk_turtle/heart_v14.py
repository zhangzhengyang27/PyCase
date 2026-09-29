"""心形曲线·森绿·v14
Turtle 绘图示例。参数化心形曲线（16sin³t 系），填充着色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.pencolor('#74c69d')
t.fillcolor('#1b4332')
t.penup()
first = True
for i in range(0, 720):
    tval = math.pi * 2 * i / 720
    x = 16 * math.sin(tval) ** 3 * 23
    y = (13 * math.cos(tval) - 5 * math.cos(2 * tval) - 2 * math.cos(3 * tval) - math.cos(4 * tval)) * 23
    if first:
        t.goto(x, y); t.pendown(); first = False
    else:
        t.goto(x, y)
t.hideturtle()
turtle.done()
