"""旋转方阵·樱粉·v7
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(180):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(84 + i * 3.4000000000000004)
    t.left(95)
t.hideturtle()
turtle.done()
