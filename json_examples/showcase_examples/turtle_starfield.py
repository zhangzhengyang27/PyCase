"""{title}
Turtle 图形：{desc}
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

import random

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("#0b1026")
t.penup()


def draw_star(x, y, size, color):
    t.penup()
    t.goto(x, y)
    t.setheading(random.randint(0, 360))
    t.pendown()
    t.pencolor(color)
    t.fillcolor(color)
    t.begin_fill()
    for _ in range(5):
        t.forward(size)
        t.right(144)
    t.end_fill()


palette = ["#ffd76e", "#ffffff", "#9fd8ff", "#ffb3c6"]
for _ in range(40):
    draw_star(random.randint(-280, 280), random.randint(-220, 220),
              random.randint(6, 18), random.choice(palette))

t.hideturtle()
turtle.done()
