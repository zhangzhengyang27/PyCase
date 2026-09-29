"""渐变螺旋·暮色·v5
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']
for i in range(180):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 19)
    t.forward(i * 3.6)
    t.left(67)
t.hideturtle()
turtle.done()
