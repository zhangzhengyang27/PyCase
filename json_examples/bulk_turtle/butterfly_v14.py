"""蝴蝶曲线·森绿·v14
Turtle 绘图示例。极坐标蝴蝶曲线 t·e^sin t·(2cos4t−sin^5(t/12))。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(2)
t.pencolor('#74c69d')
for i in range(0, 3800):
    tval = i * 0.046
    r = math.exp(math.sin(tval)) * (2 * math.cos(4 * tval) - math.sin(tval / 12) ** 5) * 133
    t.goto(r * math.sin(tval), r * math.cos(tval))
t.hideturtle()
turtle.done()
