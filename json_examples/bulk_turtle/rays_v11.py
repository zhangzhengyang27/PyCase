"""放射光束·暖阳·v11
Turtle 绘图示例。从中心放射的多彩光束，长短交替。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for i in range(104):
    t.setheading(i * 360 / 104)
    t.pencolor(colors[i % len(colors)])
    length = 70 + (i % 5) * 38
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)
t.hideturtle()
turtle.done()
