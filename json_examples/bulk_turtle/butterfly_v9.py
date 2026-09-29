"""蝴蝶曲线·经典·v9
Turtle 绘图示例。极坐标蝴蝶曲线 t·e^sin t·(2cos4t−sin^5(t/12))。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.pencolor('#2ecc71')
for i in range(0, 2800):
    tval = i * 0.036000000000000004
    r = math.exp(math.sin(tval)) * (2 * math.cos(4 * tval) - math.sin(tval / 12) ** 5) * 103
    t.goto(r * math.sin(tval), r * math.cos(tval))
t.hideturtle()
turtle.done()
