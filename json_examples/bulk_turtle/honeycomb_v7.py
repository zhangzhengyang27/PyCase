"""六边形密铺·樱粉·v7
Turtle 绘图示例。蜂窝状六边形阵列，逐行偏移排布。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
size = 26
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
