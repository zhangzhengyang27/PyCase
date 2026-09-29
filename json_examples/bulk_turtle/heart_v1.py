"""心形曲线·经典·v1
Turtle 绘图示例。参数化心形曲线（16sin³t 系），填充着色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(2)
t.pencolor('#e74c3c')
t.fillcolor('#f1c40f')
t.penup()
first = True
for i in range(0, 200):
    tval = math.pi * 2 * i / 200
    x = 16 * math.sin(tval) ** 3 * 10
    y = (13 * math.cos(tval) - 5 * math.cos(2 * tval) - 2 * math.cos(3 * tval) - math.cos(4 * tval)) * 10
    if first:
        t.goto(x, y); t.pendown(); first = False
    else:
        t.goto(x, y)
t.hideturtle()
turtle.done()
