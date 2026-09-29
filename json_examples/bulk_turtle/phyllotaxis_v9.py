"""向日葵点阵·经典·v9
Turtle 绘图示例。黄金角排布的点阵，半径按平方根增长。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
golden = 137.74
for i in range(780):
    r = 6.199999999999999 * math.sqrt(i)
    theta = i * golden
    t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
    ratio = i / 780
    t.pencolor(ratio, 0.7 - 0.5 * ratio, 0.15)
    t.dot(4 + i / 90)
t.hideturtle()
turtle.done()
