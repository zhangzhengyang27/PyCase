"""六边形密铺·薄荷·v4
Turtle 绘图示例。蜂窝状六边形阵列，逐行偏移排布。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
size = 20
t.penup()
for row in range(9):
    for col in range(11):
        x = col * size * 1.732 - 11 * size * 0.866
        y = row * size * 1.5 - 9 * size * 0.75
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
