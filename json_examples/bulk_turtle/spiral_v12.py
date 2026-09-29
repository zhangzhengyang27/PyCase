"""渐变螺旋·薄荷·v12
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']
for i in range(320):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 26)
    t.forward(i * 6.4)
    t.left(88)
t.hideturtle()
turtle.done()
