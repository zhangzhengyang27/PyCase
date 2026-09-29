"""向日葵点阵·樱粉·v15
Turtle 绘图示例。黄金角排布的点阵，半径按平方根增长。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.penup()
golden = 137.92
for i in range(1140):
    r = 8.0 * math.sqrt(i)
    theta = i * golden
    t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
    ratio = i / 1140
    t.pencolor(ratio, 0.7 - 0.5 * ratio, 0.15)
    t.dot(4 + i / 120)
t.hideturtle()
turtle.done()
