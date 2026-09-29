"""同心靶环·暖阳·v3
Turtle 绘图示例。等距同心圆环与交替填充配色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.penup()
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for i in range(20, 0, -1):
    t.goto(0, -i * 10)
    t.pendown()
    t.pencolor(colors[i % len(colors)])
    t.width(4)
    t.circle(i * 10)
    t.penup()
t.hideturtle()
turtle.done()
