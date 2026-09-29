"""蝴蝶曲线·樱粉·v15
Turtle 绘图示例。极坐标蝴蝶曲线 t·e^sin t·(2cos4t−sin^5(t/12))。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

import math
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.pencolor('#ffc9de')
for i in range(0, 4000):
    tval = i * 0.048
    r = math.exp(math.sin(tval)) * (2 * math.cos(4 * tval) - math.sin(tval / 12) ** 5) * 139
    t.goto(r * math.sin(tval), r * math.cos(tval))
t.hideturtle()
turtle.done()
