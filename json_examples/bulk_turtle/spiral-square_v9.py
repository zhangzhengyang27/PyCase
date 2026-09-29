"""旋转方阵·经典·v9
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(210):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(92 + i * 4.2)
    t.left(97)
t.hideturtle()
turtle.done()
