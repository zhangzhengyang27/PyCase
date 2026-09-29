"""方块旋梯·暮色·v13
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(136):
    t.pencolor(colors[i % len(colors)])
    side = 22 + i * 5.6
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(18)
    t.forward(15)
t.hideturtle()
turtle.done()
