"""旋涡星系·石墨·v8
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(17)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(5):
    for i in range(160):
        theta = i * 5.800000000000001 + arm * 360 / 5
        r = 11 * math.exp(0.063 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(3, "'#868e96'")
t.hideturtle()
turtle.done()
