"""烟花绽放·经典·v1
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import random
random.seed(50)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for burst in range(6):
    cx, cy = random.randint(-240, 240), random.randint(-100, 240 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(40):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(18, 48))
        t.penup()
t.hideturtle()
turtle.done()
