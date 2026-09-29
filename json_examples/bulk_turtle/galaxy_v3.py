"""旋涡星系·暖阳·v3
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(12)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(4):
    for i in range(110):
        theta = i * 3.8 + arm * 360 / 4
        r = 6 * math.exp(0.043000000000000003 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(4, "'#ff006e'")
t.hideturtle()
turtle.done()
