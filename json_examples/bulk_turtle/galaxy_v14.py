"""旋涡星系·森绿·v14
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(23)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(3):
    for i in range(220):
        theta = i * 8.2 + arm * 360 / 3
        r = 17 * math.exp(0.08700000000000001 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(3, "'#74c69d'")
t.hideturtle()
turtle.done()
