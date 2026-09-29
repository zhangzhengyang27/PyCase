"""利萨如曲线·暮色·v5
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(2)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
a, b, delta = 1, 5, 1.6
for i in range(0, 920):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(194 * math.sin(a * tval + delta), 162 * math.sin(b * tval))
t.hideturtle()
turtle.done()
