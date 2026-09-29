"""旋转方阵·暮色·v5
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(150):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(76 + i * 2.6)
    t.left(93)
t.hideturtle()
turtle.done()
