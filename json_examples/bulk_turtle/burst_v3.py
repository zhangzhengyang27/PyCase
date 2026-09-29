"""烟花绽放·暖阳·v3
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import random
random.seed(52)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for burst in range(8):
    cx, cy = random.randint(-256, 256), random.randint(-100, 256 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(52):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(22, 56))
        t.penup()
t.hideturtle()
turtle.done()
