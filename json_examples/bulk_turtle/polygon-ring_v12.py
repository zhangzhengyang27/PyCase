"""多边形环·薄荷·v12
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
sides, length = 8, 136
for i in range(25):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 7.5)
        t.left(360 / sides)
    t.left(16)
    t.forward(15)
t.hideturtle()
turtle.done()
