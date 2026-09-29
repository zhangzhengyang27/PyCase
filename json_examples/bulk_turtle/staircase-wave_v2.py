"""阶梯波·海雾·v2
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for cycle in range(4):
    for s in range(7):
        t.pencolor(colors[s % len(colors)])
        t.forward(13)
        t.left(90)
        t.forward(7)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -44)
    t.pendown()
t.hideturtle()
turtle.done()
