"""旋涡星系·森绿·v6
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(15)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(3):
    for i in range(140):
        theta = i * 5.0 + arm * 360 / 3
        r = 9 * math.exp(0.05500000000000001 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(4, "'#1b4332'")
t.hideturtle()
turtle.done()
