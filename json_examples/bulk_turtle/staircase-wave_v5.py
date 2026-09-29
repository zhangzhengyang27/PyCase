"""阶梯波·暮色·v5
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for cycle in range(3):
    for s in range(10):
        t.pencolor(colors[s % len(colors)])
        t.forward(16)
        t.left(90)
        t.forward(10)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -56)
    t.pendown()
t.hideturtle()
turtle.done()
