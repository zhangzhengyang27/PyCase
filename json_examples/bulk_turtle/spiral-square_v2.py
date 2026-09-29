"""旋转方阵·海雾·v2
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for i in range(105):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(64 + i * 1.4)
    t.left(90)
t.hideturtle()
turtle.done()
