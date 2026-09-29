"""方块旋梯·海雾·v10
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for i in range(112):
    t.pencolor(colors[i % len(colors)])
    side = 19 + i * 4.699999999999999
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(15)
    t.forward(12)
t.hideturtle()
turtle.done()
