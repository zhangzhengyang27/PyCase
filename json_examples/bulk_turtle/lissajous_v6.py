"""利萨如曲线·森绿·v6
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
a, b, delta = 2, 2, 2.0
for i in range(0, 1000):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(200 * math.sin(a * tval + delta), 170 * math.sin(b * tval))
t.hideturtle()
turtle.done()
