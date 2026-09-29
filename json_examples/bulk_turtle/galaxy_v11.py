"""旋涡星系·暖阳·v11
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(20)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(4):
    for i in range(190):
        theta = i * 7.0 + arm * 360 / 4
        r = 14 * math.exp(0.07500000000000001 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(3, "'#ffbe0b'")
t.hideturtle()
turtle.done()
