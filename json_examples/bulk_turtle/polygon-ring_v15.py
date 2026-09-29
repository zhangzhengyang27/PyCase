"""多边形环·樱粉·v15
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
sides, length = 5, 154
for i in range(28):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 9.0)
        t.left(360 / sides)
    t.left(19)
    t.forward(18)
t.hideturtle()
turtle.done()
