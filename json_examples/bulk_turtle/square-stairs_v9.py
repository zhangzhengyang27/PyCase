"""方块旋梯·经典·v9
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(104):
    t.pencolor(colors[i % len(colors)])
    side = 18 + i * 4.4
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(14)
    t.forward(11)
t.hideturtle()
turtle.done()
