"""渐变螺旋·薄荷·v4
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for i in range(160):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 18)
    t.forward(i * 3.2)
    t.left(64)
t.hideturtle()
turtle.done()
