"""方块旋梯·暖阳·v3
Turtle 绘图示例。边长渐变的正方形旋转堆叠出楼梯结构。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for i in range(56):
    t.pencolor(colors[i % len(colors)])
    side = 12 + i * 2.6
    for _ in range(4):
        t.forward(side)
        t.right(90)
    t.right(8)
    t.forward(5)
t.hideturtle()
turtle.done()
