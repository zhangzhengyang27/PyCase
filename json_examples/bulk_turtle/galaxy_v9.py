"""旋涡星系·经典·v9
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(18)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(2):
    for i in range(170):
        theta = i * 6.2 + arm * 360 / 2
        r = 12 * math.exp(0.067 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(4, "'#2ecc71'")
t.hideturtle()
turtle.done()
