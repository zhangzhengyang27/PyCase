"""利萨如曲线·暖阳·v3
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
a, b, delta = 3, 6, 0.8
for i in range(0, 760):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(182 * math.sin(a * tval + delta), 146 * math.sin(b * tval))
t.hideturtle()
turtle.done()
