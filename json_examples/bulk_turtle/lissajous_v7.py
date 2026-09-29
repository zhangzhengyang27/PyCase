"""利萨如曲线·樱粉·v7
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
a, b, delta = 3, 4, 2.4000000000000004
for i in range(0, 1080):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(206 * math.sin(a * tval + delta), 178 * math.sin(b * tval))
t.hideturtle()
turtle.done()
