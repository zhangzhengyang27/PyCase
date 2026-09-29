"""放射光束·石墨·v8
Turtle 绘图示例。从中心放射的多彩光束，长短交替。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for i in range(80):
    t.setheading(i * 360 / 80)
    t.pencolor(colors[i % len(colors)])
    length = 58 + (i % 5) * 32
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)
t.hideturtle()
turtle.done()
