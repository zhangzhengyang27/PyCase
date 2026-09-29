"""放射光束·樱粉·v15
Turtle 绘图示例。从中心放射的多彩光束，长短交替。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(136):
    t.setheading(i * 360 / 136)
    t.pencolor(colors[i % len(colors)])
    length = 86 + (i % 6) * 46
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)
t.hideturtle()
turtle.done()
