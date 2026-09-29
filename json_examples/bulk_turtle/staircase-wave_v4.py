"""阶梯波·薄荷·v4
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for cycle in range(6):
    for s in range(9):
        t.pencolor(colors[s % len(colors)])
        t.forward(15)
        t.left(90)
        t.forward(9)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -52)
    t.pendown()
t.hideturtle()
turtle.done()
