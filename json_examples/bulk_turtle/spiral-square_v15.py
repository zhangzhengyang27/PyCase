"""旋转方阵·樱粉·v15
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(300):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(116 + i * 6.6000000000000005)
    t.left(103)
t.hideturtle()
turtle.done()
