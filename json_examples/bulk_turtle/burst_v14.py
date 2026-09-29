"""烟花绽放·森绿·v14
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import random
random.seed(63)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for burst in range(7):
    cx, cy = random.randint(-344, 344), random.randint(-100, 344 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(118):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(44, 100))
        t.penup()
t.hideturtle()
turtle.done()
