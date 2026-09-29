"""旋涡星系·海雾·v2
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(11)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(3):
    for i in range(100):
        theta = i * 3.4 + arm * 360 / 3
        r = 5 * math.exp(0.03900000000000001 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(3, "'#087e8b'")
t.hideturtle()
turtle.done()
