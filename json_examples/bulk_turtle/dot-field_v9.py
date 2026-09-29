"""点密度场·经典·v9
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(48)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1140):
    x = random.randint(-324, 324)
    y = random.randint(-324 * 0.7, 324 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(7 * (1 - d / (324 * 1.2)))), "'#2ecc71'")
t.hideturtle()
turtle.done()
