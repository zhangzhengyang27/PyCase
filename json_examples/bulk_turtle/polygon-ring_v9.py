"""多边形环·经典·v9
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
sides, length = 5, 118
for i in range(22):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 6.0)
        t.left(360 / sides)
    t.left(13)
    t.forward(12)
t.hideturtle()
turtle.done()
