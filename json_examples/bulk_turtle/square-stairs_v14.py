"""方块旋梯·森绿·v14
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for i in range(144):
    t.pencolor(colors[i % len(colors)])
    side = 23 + i * 5.9
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(19)
    t.forward(16)
t.hideturtle()
turtle.done()
