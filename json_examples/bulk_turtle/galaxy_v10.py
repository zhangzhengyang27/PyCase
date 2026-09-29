"""旋涡星系·海雾·v10
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(19)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(3):
    for i in range(180):
        theta = i * 6.6 + arm * 360 / 3
        r = 13 * math.exp(0.07100000000000001 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(2, "'#c81d25'")
t.hideturtle()
turtle.done()
