"""渐变螺旋·海雾·v10
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']
for i in range(280):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 24)
    t.forward(i * 5.6)
    t.left(82)
t.hideturtle()
turtle.done()
