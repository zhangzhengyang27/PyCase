"""点密度场·经典·v1
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(40)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(500):
    x = random.randint(-260, 260)
    y = random.randint(int(-260 * 0.7), int(260 * 0.7))
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(7 * (1 - d / (260 * 1.2)))), "#e74c3c")
t.hideturtle()
turtle.done()
