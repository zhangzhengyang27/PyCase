"""阶梯波·樱粉·v7
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for cycle in range(5):
    for s in range(7):
        t.pencolor(colors[s % len(colors)])
        t.forward(18)
        t.left(90)
        t.forward(12)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -64)
    t.pendown()
t.hideturtle()
turtle.done()
