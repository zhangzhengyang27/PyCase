"""旋涡星系·樱粉·v7
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(16)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(4):
    for i in range(150):
        theta = i * 5.4 + arm * 360 / 4
        r = 10 * math.exp(0.059000000000000004 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(2, "'#ffc2d1'")
t.hideturtle()
turtle.done()
