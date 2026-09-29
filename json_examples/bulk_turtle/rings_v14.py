"""同心靶环·森绿·v14
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for i in range(42, 0, -1):
    t.goto(0, -i * 21)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(3)
    t.circle(i * 21)
    t.penup()
t.hideturtle()
turtle.done()
