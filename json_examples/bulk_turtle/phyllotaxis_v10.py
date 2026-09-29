"""向日葵点阵·海雾·v10
Turtle 绘图示例。黄金角排布的点阵，半径按平方根增长。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.penup()
golden = 137.77
for i in range(840):
    r = 6.5 * math.sqrt(i)
    theta = i * golden
    t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
    ratio = i / 840
    t.pencolor(ratio, 0.7 - 0.5 * ratio, 0.15)
    t.dot(2 + i / 95)
t.hideturtle()
turtle.done()
