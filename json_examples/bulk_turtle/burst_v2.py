"""烟花绽放·海雾·v2
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import random
random.seed(51)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for burst in range(7):
    cx, cy = random.randint(-248, 248), random.randint(-100, 248 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(46):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(20, 52))
        t.penup()
t.hideturtle()
turtle.done()
