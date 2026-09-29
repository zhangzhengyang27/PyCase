"""点密度场·樱粉·v7
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(46)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(980):
    x = random.randint(-308, 308)
    y = random.randint(-308 * 0.7, 308 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(9 * (1 - d / (308 * 1.2)))), "'#ffc2d1'")
t.hideturtle()
turtle.done()
