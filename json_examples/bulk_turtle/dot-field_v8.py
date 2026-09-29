"""点密度场·石墨·v8
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math, random
random.seed(47)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1060):
    x = random.randint(-316, 316)
    y = random.randint(-316 * 0.7, 316 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(10 * (1 - d / (316 * 1.2)))), "'#868e96'")
t.hideturtle()
turtle.done()
