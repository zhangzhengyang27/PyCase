"""对称曼陀罗·樱粉·v7
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']

def petal():
    for _ in range(7):
        t.forward(76)
        t.right(84)

for ring in range(5):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(12):
        petal()
        t.right(360 // 12)
    t.right(16)
    t.forward(12)
t.hideturtle()
turtle.done()
