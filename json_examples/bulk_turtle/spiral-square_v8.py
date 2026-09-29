"""旋转方阵·石墨·v8
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for i in range(195):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(88 + i * 3.8000000000000003)
    t.left(96)
t.hideturtle()
turtle.done()
