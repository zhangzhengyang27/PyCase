"""旋涡星系·樱粉·v15
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(24)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(4):
    for i in range(230):
        theta = i * 8.600000000000001 + arm * 360 / 4
        r = 18 * math.exp(0.091 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(4, "'#ffc9de'")
t.hideturtle()
turtle.done()
