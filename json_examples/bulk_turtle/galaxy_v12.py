"""旋涡星系·薄荷·v12
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(21)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(5):
    for i in range(200):
        theta = i * 7.4 + arm * 360 / 5
        r = 15 * math.exp(0.079 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(4, "'#72efdd'")
t.hideturtle()
turtle.done()
