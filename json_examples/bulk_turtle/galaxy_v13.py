"""旋涡星系·暮色·v13
Turtle 绘图示例。对数螺线旋臂 + 中心密集点组成的星系。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(22)
t = turtle.Turtle()
t.speed(0)
t.penup()
for arm in range(2):
    for i in range(210):
        theta = i * 7.800000000000001 + arm * 360 / 2
        r = 16 * math.exp(0.083 * i)
        t.goto(r * math.cos(math.radians(theta)), r * math.sin(math.radians(theta)))
        t.dot(2, "'#edf2f4'")
t.hideturtle()
turtle.done()
