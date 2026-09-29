"""六角花·樱粉·v7
Turtle 绘图示例。绕中心旋转的六边形花瓣簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
size = 64
for petal in range(30):
    t.pencolor(colors[petal % len(colors)])
    t.pensize(1 + petal % 3)
    for _ in range(6):
        t.forward(size)
        t.left(60)
    t.forward(size)
    t.left(24)
t.hideturtle()
turtle.done()
