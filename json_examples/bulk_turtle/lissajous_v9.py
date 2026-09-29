"""利萨如曲线·经典·v9
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
a, b, delta = 1, 3, 3.2
for i in range(0, 1240):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(218 * math.sin(a * tval + delta), 194 * math.sin(b * tval))
t.hideturtle()
turtle.done()
