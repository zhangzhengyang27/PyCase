"""六角花·经典·v9
Turtle 绘图示例。绕中心旋转的六边形花瓣簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
size = 72
for petal in range(36):
    t.pencolor(colors[petal % len(colors)])
    t.pensize(1 + petal % 3)
    for _ in range(6):
        t.forward(size)
        t.left(60)
    t.forward(size)
    t.left(22)
t.hideturtle()
turtle.done()
