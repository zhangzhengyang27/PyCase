"""旋转方阵·薄荷·v12
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for i in range(255):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(104 + i * 5.4)
    t.left(100)
t.hideturtle()
turtle.done()
