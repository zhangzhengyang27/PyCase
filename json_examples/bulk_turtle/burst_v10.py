"""烟花绽放·海雾·v10
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import random
random.seed(59)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for burst in range(7):
    cx, cy = random.randint(-312, 312), random.randint(-100, 312 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(94):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(36, 84))
        t.penup()
t.hideturtle()
turtle.done()
