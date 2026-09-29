"""点密度场·森绿·v6
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(45)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(900):
    x = random.randint(-300, 300)
    y = random.randint(-300 * 0.7, 300 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(8 * (1 - d / (300 * 1.2)))), "'#1b4332'")
t.hideturtle()
turtle.done()
