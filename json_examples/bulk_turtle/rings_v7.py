"""同心靶环·樱粉·v7
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(28, 0, -1):
    t.goto(0, -i * 14)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(4)
    t.circle(i * 14)
    t.penup()
t.hideturtle()
turtle.done()
