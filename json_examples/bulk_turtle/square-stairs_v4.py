"""方块旋梯·薄荷·v4
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for i in range(64):
    t.pencolor(colors[i % len(colors)])
    side = 13 + i * 2.9
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(9)
    t.forward(6)
t.hideturtle()
turtle.done()
