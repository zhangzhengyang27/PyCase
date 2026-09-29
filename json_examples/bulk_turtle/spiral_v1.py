"""渐变螺旋·经典·v1
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
for i in range(100):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 15)
    t.forward(i * 2.0)
    t.left(55)
t.hideturtle()
turtle.done()
