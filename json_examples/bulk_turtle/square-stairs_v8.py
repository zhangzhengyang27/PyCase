"""方块旋梯·石墨·v8
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for i in range(96):
    t.pencolor(colors[i % len(colors)])
    side = 17 + i * 4.1
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(13)
    t.forward(10)
t.hideturtle()
turtle.done()
