"""点密度场·薄荷·v12
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(51)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1380):
    x = random.randint(-348, 348)
    y = random.randint(-348 * 0.7, 348 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(10 * (1 - d / (348 * 1.2)))), "'#72efdd'")
t.hideturtle()
turtle.done()
