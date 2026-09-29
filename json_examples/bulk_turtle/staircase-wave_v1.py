"""阶梯波·经典·v1
Turtle 绘图示例。阶梯递升再回落的周期折线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for cycle in range(3):
    for s in range(6):
        t.pencolor(colors[s % len(colors)])
        t.forward(12)
        t.left(90)
        t.forward(6)
        t.right(90)
    t.penup()
    t.goto(-200, (cycle + 1) * -40)
    t.pendown()
t.hideturtle()
turtle.done()
