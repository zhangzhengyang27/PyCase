"""方块旋梯·海雾·v2
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for i in range(48):
    t.pencolor(colors[i % len(colors)])
    side = 11 + i * 2.3
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(7)
    t.forward(4)
t.hideturtle()
turtle.done()
