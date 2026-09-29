"""渐变螺旋·暮色·v13
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(340):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 27)
    t.forward(i * 6.800000000000001)
    t.left(91)
t.hideturtle()
turtle.done()
