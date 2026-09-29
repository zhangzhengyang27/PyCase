"""玫瑰线·石墨·v8
Turtle 绘图示例。极坐标玫瑰线 r = R·sin(k·θ)，k 控制花瓣数。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(2)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
k, R = 4, 204
for i in range(0, 361, 2):
    rad = math.radians(i)
    r = R * math.sin(k * rad)
    t.pencolor(colors[(i // 30) % len(colors)])
    t.goto(r * math.cos(rad), r * math.sin(rad))
t.hideturtle()
turtle.done()
