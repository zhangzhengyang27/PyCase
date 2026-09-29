"""同心靶环·薄荷·v4
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for i in range(22, 0, -1):
    t.goto(0, -i * 11)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(5)
    t.circle(i * 11)
    t.penup()
t.hideturtle()
turtle.done()
