"""向日葵点阵·海雾·v2
Turtle 绘图示例。黄金角排布的点阵，半径按平方根增长。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
golden = 137.53
for i in range(360):
    r = 4.1 * math.sqrt(i)
    theta = i * golden
    t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
    ratio = i / 360
    t.pencolor(ratio, 0.7 - 0.5 * ratio, 0.15)
    t.dot(3 + i / 55)
t.hideturtle()
turtle.done()
