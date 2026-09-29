"""阶梯波·暖阳·v11
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for cycle in range(5):
    for s in range(6):
        t.pencolor(colors[s % len(colors)])
        t.forward(22)
        t.left(90)
        t.forward(16)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -80)
    t.pendown()
t.hideturtle()
turtle.done()
