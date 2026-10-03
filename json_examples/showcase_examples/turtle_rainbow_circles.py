"""彩虹同心圆
Turtle 图形：HSV 颜色空间渐变填充同心圆，演示 colorsys 与 begin_fill/end_fill。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

import colorsys

t = turtle.Turtle()
t.speed(0)
t.penup()

for i in range(36):
    r, g, b = colorsys.hsv_to_rgb(i / 36, 0.9, 1.0)
    t.pencolor(r, g, b)
    t.fillcolor(r, g, b)
    t.sety(-i * 4)
    t.pendown()
    t.begin_fill()
    t.circle(20 + i * 4)
    t.end_fill()
    t.penup()

t.hideturtle()
turtle.done()
