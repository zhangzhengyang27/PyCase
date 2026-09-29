"""放射光束·暮色·v5
Turtle 绘图示例。从中心放射的多彩光束，长短交替。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(56):
    t.setheading(i * 360 / 56)
    t.pencolor(colors[i % len(colors)])
    length = 46 + (i % 5) * 26
    t.pendown()
    t.forward(length)
    t.penup()
    t.backward(length)
t.hideturtle()
turtle.done()
