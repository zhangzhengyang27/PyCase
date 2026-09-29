"""旋转方阵·暖阳·v11
Turtle 绘图示例。正方形逐层旋转放大的涡旋结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for i in range(240):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 2)
    t.forward(100 + i * 5.0)
    t.left(99)
t.hideturtle()
turtle.done()
