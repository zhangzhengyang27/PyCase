"""多边形环·海雾·v10
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
sides, length = 6, 124
for i in range(23):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 6.5)
        t.left(360 / sides)
    t.left(14)
    t.forward(13)
t.hideturtle()
turtle.done()
