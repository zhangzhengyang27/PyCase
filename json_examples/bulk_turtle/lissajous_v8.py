"""利萨如曲线·石墨·v8
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(2)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
a, b, delta = 4, 6, 2.8000000000000003
for i in range(0, 1160):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(212 * math.sin(a * tval + delta), 186 * math.sin(b * tval))
t.hideturtle()
turtle.done()
