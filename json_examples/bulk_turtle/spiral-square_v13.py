"""旋转方阵·暮色·v13
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(270):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(108 + i * 5.800000000000001)
    t.left(101)
t.hideturtle()
turtle.done()
