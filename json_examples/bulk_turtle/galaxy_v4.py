"""旋涡星系·薄荷·v4
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(13)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(5):
    for i in range(120):
        theta = i * 4.2 + arm * 360 / 5
        r = 7 * math.exp(0.047 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(2, "'#48bfe3'")
t.hideturtle()
turtle.done()
