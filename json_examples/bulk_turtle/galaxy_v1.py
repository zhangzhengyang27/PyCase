"""旋涡星系·经典·v1
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(10)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(2):
    for i in range(90):
        theta = i * 3.0 + arm * 360 / 2
        r = 4 * math.exp(0.035 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(2, "'#e74c3c'")
t.hideturtle()
turtle.done()
