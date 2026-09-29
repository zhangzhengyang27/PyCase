"""蝴蝶曲线·薄荷·v4
Turtle 绘图示例。极坐标蝴蝶曲线 t·e^sin t·(2cos4t−sin^5(t/12))。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
import math
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
t.pencolor('#48bfe3')
for i in range(0, 1800):
    tval = i * 0.026000000000000002
    r = math.exp(math.sin(tval)) * (2 * math.cos(4 * tval) - math.sin(tval / 12) ** 5) * 73
    t.goto(r * math.sin(tval), r * math.cos(tval))
t.hideturtle()
turtle.done()
