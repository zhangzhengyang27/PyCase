"""心形曲线·樱粉·v7
Turtle 绘图示例。参数化心形曲线（16sin³t 系），填充着色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(2)
t.pencolor('#ffc2d1')
t.fillcolor('#fb6f92')
t.penup()
first = True
for i in range(0, 440):
    tval = math.pi * 2 * i / 440
    x = 16 * math.sin(tval) ** 3 * 16
    y = (13 * math.cos(tval) - 5 * math.cos(2 * tval) - 2 * math.cos(3 * tval) - math.cos(4 * tval)) * 16
    if first:
        t.goto(x, y); t.pendown(); first = False
    else:
        t.goto(x, y)
t.hideturtle()
turtle.done()
