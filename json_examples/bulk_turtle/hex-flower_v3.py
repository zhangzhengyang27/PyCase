"""六角花·暖阳·v3
Turtle 绘图示例。绕中心旋转的六边形花瓣簇。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
size = 48
for petal in range(18):
    t.pencolor(colors[petal % len(colors)])
    t.pensize(1 + petal % 3)
    for _ in range(6):
        t.forward(size)
        t.left(60)
    t.forward(size)
    t.left(28)
t.hideturtle()
turtle.done()
