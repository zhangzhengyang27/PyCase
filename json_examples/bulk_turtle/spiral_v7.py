"""渐变螺旋·樱粉·v7
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']
for i in range(220):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 21)
    t.forward(i * 4.4)
    t.left(73)
t.hideturtle()
turtle.done()
