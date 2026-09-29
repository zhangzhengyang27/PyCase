"""多边形环·暖阳·v3
Turtle 绘图示例。旋转内接多边形形成的光环结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
sides, length = 5, 82
for i in range(16):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i % 3)
    for _ in range(sides):
        t.forward(length + i * 3.0)
        t.left(360 / sides)
    t.left(7)
    t.forward(6)
t.hideturtle()
turtle.done()
