"""烟花绽放·石墨·v8
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import random
random.seed(57)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for burst in range(9):
    cx, cy = random.randint(-296, 296), random.randint(-100, 296 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(82):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(32, 76))
        t.penup()
t.hideturtle()
turtle.done()
