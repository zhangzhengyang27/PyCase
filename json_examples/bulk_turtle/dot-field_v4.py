"""点密度场·薄荷·v4
Turtle 绘图示例。按噪声式密度函数布点的圆点场。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math, random
random.seed(43)
t = turtle.Turtle()
t.speed(0)
t.penup()
for _ in range(740):
    x = random.randint(-284, 284)
    y = random.randint(-284 * 0.7, 284 * 0.7)
    d = math.hypot(x, y)
    t.goto(x, y)
    t.dot(max(1, int(10 * (1 - d / (284 * 1.2)))), "'#48bfe3'")
t.hideturtle()
turtle.done()
