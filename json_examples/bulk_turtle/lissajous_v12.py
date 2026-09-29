"""利萨如曲线·薄荷·v12
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
a, b, delta = 4, 4, 4.4
for i in range(0, 1480):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(236 * math.sin(a * tval + delta), 218 * math.sin(b * tval))
t.hideturtle()
turtle.done()
