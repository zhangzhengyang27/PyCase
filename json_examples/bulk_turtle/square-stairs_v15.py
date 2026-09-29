"""方块旋梯·樱粉·v15
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(152):
    t.pencolor(colors[i % len(colors)])
    side = 24 + i * 6.2
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(20)
    t.forward(17)
t.hideturtle()
turtle.done()
