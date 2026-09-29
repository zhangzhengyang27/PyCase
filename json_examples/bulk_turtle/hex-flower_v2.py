"""六角花·海雾·v2
Turtle 绘图示例。绕中心旋转的六边形花瓣簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
size = 44
for petal in range(15):
    t.pencolor(colors[petal % len(colors)])
    t.pensize(1 + petal % 3)
    for _ in range(6):
        t.forward(size)
        t.left(60)
    t.forward(size)
    t.left(29)
t.hideturtle()
turtle.done()
