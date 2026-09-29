"""阶梯波·薄荷·v12
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for cycle in range(6):
    for s in range(7):
        t.pencolor(colors[s % len(colors)])
        t.forward(23)
        t.left(90)
        t.forward(17)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -84)
    t.pendown()
t.hideturtle()
turtle.done()
