"""放射光束·经典·v1
Turtle 绘图示例。从中心放射的多彩光束，长短交替。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(24):
    t.setheading(i * 360 / 24)
    t.pencolor(colors[i % len(colors)])
    length = 30 + (i % 4) * 18
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)
t.hideturtle()
turtle.done()
