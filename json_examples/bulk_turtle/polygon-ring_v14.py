"""多边形环·森绿·v14
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
sides, length = 4, 148
for i in range(27):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 8.5)
        t.left(360 / sides)
    t.left(18)
    t.forward(17)
t.hideturtle()
turtle.done()
