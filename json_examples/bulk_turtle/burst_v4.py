"""烟花绽放·薄荷·v4
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import random
random.seed(53)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for burst in range(9):
    cx, cy = random.randint(-264, 264), random.randint(-100, 264 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(58):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(24, 60))
        t.penup()
t.hideturtle()
turtle.done()
