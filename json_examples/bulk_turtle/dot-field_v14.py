"""点密度场·森绿·v14
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(53)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1540):
    x = random.randint(-364, 364)
    y = random.randint(-364 * 0.7, 364 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(8 * (1 - d / (364 * 1.2)))), "'#74c69d'")
t.hideturtle()
turtle.done()
