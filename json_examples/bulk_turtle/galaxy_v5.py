"""旋涡星系·暮色·v5
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(14)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(2):
    for i in range(130):
        theta = i * 4.6 + arm * 360 / 2
        r = 8 * math.exp(0.051000000000000004 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(3, "'#d90429'")
t.hideturtle()
turtle.done()
