"""同心靶环·石墨·v8
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for i in range(30, 0, -1):
    t.goto(0, -i * 15)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(5)
    t.circle(i * 15)
    t.penup()
t.hideturtle()
turtle.done()
