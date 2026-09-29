"""利萨如曲线·海雾·v10
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
a, b, delta = 2, 5, 3.6
for i in range(0, 1320):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(224 * math.sin(a * tval + delta), 202 * math.sin(b * tval))
t.hideturtle()
turtle.done()
