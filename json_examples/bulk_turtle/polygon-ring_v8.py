"""多边形环·石墨·v8
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
sides, length = 4, 112
for i in range(21):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 5.5)
        t.left(360 / sides)
    t.left(12)
    t.forward(11)
t.hideturtle()
turtle.done()
