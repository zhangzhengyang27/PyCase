"""点密度场·海雾·v2
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(41)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(580):
    x = random.randint(-268, 268)
    y = random.randint(-268 * 0.7, 268 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(8 * (1 - d / (268 * 1.2)))), "'#087e8b'")
t.hideturtle()
turtle.done()
