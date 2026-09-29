"""渐变螺旋·暖阳·v11
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']
for i in range(300):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 25)
    t.forward(i * 6.0)
    t.left(85)
t.hideturtle()
turtle.done()
