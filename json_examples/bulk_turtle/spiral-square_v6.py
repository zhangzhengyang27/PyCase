"""旋转方阵·森绿·v6
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for i in range(165):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(80 + i * 3.0)
    t.left(94)
t.hideturtle()
turtle.done()
