"""烟花绽放·经典·v9
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import random
random.seed(58)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for burst in range(6):
    cx, cy = random.randint(-304, 304), random.randint(-100, 304 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(88):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(34, 80))
        t.penup()
t.hideturtle()
turtle.done()
