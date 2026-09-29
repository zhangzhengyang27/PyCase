"""利萨如曲线·暮色·v13
Turtle 绘图示例。参数方程 x=A·sin(a·t+δ), y=B·sin(b·t) 的交织曲线。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
a, b, delta = 1, 6, 4.800000000000001
for i in range(0, 1560):
    tval = i * 0.03
    t.pencolor(colors[i % len(colors)])
    t.goto(242 * math.sin(a * tval + delta), 226 * math.sin(b * tval))
t.hideturtle()
turtle.done()
