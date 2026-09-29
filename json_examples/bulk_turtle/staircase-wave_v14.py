"""阶梯波·森绿·v14
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for cycle in range(4):
    for s in range(9):
        t.pencolor(colors[s % len(colors)])
        t.forward(25)
        t.left(90)
        t.forward(19)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -92)
    t.pendown()
t.hideturtle()
turtle.done()
