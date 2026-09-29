"""点密度场·樱粉·v15
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(54)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1620):
    x = random.randint(-372, 372)
    y = random.randint(-372 * 0.7, 372 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(9 * (1 - d / (372 * 1.2)))), "'#ffc9de'")
t.hideturtle()
turtle.done()
