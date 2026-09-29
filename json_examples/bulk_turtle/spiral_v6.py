"""渐变螺旋·森绿·v6
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']
for i in range(200):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 20)
    t.forward(i * 4.0)
    t.left(70)
t.hideturtle()
turtle.done()
