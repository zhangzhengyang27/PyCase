"""数学玫瑰线
Turtle 图形：参数方程 petals 瓣玫瑰线，体会极坐标与循环角度的对应关系。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

import math

t = turtle.Turtle()
t.speed(0)
t.pensize(2)
petals = 5

for i in range(361):
    rad = math.radians(i)
    r = 150 * math.sin(petals * rad)
    x, y = r * math.cos(rad), r * math.sin(rad)
    t.goto(x, y)

t.hideturtle()
turtle.done()
