"""六边形密铺·暖阳·v11
Turtle 绘图示例。蜂窝状六边形阵列，逐行偏移排布。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
size = 34
t.penup()
for row in range(8):
    for col in range(10):
        x = col * size * 1.732 - 10 * size * 0.866
        y = row * size * 1.5 - 8 * size * 0.75
        t.goto(x + (row % 2) * size * 0.866, y)
        t.setheading(0)
        t.pendown()
        t.pencolor(colors[(row + col) % len(colors)])
        for _ in range(6):
            t.forward(size)
            t.left(60)
        t.penup()
t.hideturtle()
turtle.done()
