"""阶梯波·石墨·v8
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for cycle in range(6):
    for s in range(8):
        t.pencolor(colors[s % len(colors)])
        t.forward(19)
        t.left(90)
        t.forward(13)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -68)
    t.pendown()
t.hideturtle()
turtle.done()
