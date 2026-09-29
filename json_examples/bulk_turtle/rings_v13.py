"""同心靶环·暮色·v13
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(40, 0, -1):
    t.goto(0, -i * 20)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(2)
    t.circle(i * 20)
    t.penup()
t.hideturtle()
turtle.done()
