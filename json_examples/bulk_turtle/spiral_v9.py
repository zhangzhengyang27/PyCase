"""渐变螺旋·经典·v9
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(260):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 23)
    t.forward(i * 5.2)
    t.left(79)
t.hideturtle()
turtle.done()
