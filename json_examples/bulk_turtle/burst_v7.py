"""烟花绽放·樱粉·v7
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import random
random.seed(56)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for burst in range(8):
    cx, cy = random.randint(-288, 288), random.randint(-100, 288 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(76):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(30, 72))
        t.penup()
t.hideturtle()
turtle.done()
