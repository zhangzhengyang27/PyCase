"""同心靶环·海雾·v10
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for i in range(34, 0, -1):
    t.goto(0, -i * 17)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(3)
    t.circle(i * 17)
    t.penup()
t.hideturtle()
turtle.done()
