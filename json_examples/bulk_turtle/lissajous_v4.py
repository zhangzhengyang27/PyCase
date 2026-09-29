"""利萨如曲线·薄荷·v4
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
a, b, delta = 4, 3, 1.2000000000000002
for i in range(0, 840):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(188 * math.sin(a * tval + delta), 154 * math.sin(b * tval))
t.hideturtle()
turtle.done()
