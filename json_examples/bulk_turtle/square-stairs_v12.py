"""方块旋梯·薄荷·v12
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for i in range(128):
    t.pencolor(colors[i % len(colors)])
    side = 21 + i * 5.3
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(17)
    t.forward(14)
t.hideturtle()
turtle.done()
