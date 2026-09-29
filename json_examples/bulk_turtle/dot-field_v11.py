"""点密度场·暖阳·v11
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(50)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1300):
    x = random.randint(-340, 340)
    y = random.randint(-340 * 0.7, 340 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(9 * (1 - d / (340 * 1.2)))), "'#ffbe0b'")
t.hideturtle()
turtle.done()
