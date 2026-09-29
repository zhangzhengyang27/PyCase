"""同心靶环·经典·v9
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(32, 0, -1):
    t.goto(0, -i * 16)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(2)
    t.circle(i * 16)
    t.penup()
t.hideturtle()
turtle.done()
