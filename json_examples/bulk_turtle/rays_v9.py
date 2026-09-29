"""放射光束·经典·v9
Turtle 绘图示例。从中心放射的多彩光束，长短交替。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(88):
    t.setheading(i * 360 / 88)
    t.pencolor(colors[i % len(colors)])
    length = 62 + (i % 6) * 34
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)
t.hideturtle()
turtle.done()
