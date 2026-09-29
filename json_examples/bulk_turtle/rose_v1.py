"""玫瑰线·经典·v1
Turtle 绘图示例。极坐标玫瑰线 r = R·sin(k·θ)，k 控制花瓣数。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
k, R = 2, 120
for i in range(0, 361, 2):
    rad = math.radians(i)
    r = R * math.sin(k * rad)
    t.pencolor(colors[(i // 30) % len(colors)])
    t.goto(r * math.cos(rad), r * math.sin(rad))
t.hideturtle()
turtle.done()
