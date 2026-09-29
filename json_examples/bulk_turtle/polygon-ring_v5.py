"""多边形环·暮色·v5
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
sides, length = 7, 94
for i in range(18):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 4.0)
        t.left(360 / sides)
    t.left(9)
    t.forward(8)
t.hideturtle()
turtle.done()
