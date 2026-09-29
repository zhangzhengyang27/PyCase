"""方块旋梯·樱粉·v7
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(88):
    t.pencolor(colors[i % len(colors)])
    side = 16 + i * 3.8
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(12)
    t.forward(9)
t.hideturtle()
turtle.done()
