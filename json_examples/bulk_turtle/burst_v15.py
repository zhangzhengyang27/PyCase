"""烟花绽放·樱粉·v15
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import random
random.seed(64)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for burst in range(8):
    cx, cy = random.randint(-352, 352), random.randint(-100, 352 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(124):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(46, 104))
        t.penup()
t.hideturtle()
turtle.done()
