"""点密度场·暮色·v13
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(52)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(1460):
    x = random.randint(-356, 356)
    y = random.randint(-356 * 0.7, 356 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(7 * (1 - d / (356 * 1.2)))), "'#edf2f4'")
t.hideturtle()
turtle.done()
