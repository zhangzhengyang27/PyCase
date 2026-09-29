"""烟花绽放·暮色·v13
Turtle 绘图示例。多中心随机放射线组成的烟花簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import random
random.seed(62)
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for burst in range(6):
    cx, cy = random.randint(-336, 336), random.randint(-100, 336 * 0.6)
    color = colors[burst % len(colors)]
    for _ in range(112):
        t.goto(cx, cy)
        t.setheading(random.randint(0, 360))
        t.pendown()
        t.forward(random.randint(42, 96))
        t.penup()
t.hideturtle()
turtle.done()
