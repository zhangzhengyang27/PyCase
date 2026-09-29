"""对称曼陀罗·海雾·v2
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']

def petal():
    for _ in range(6):
        t.forward(46)
        t.right(64)

for ring in range(6):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(11):
        petal()
        t.right(360 // 11)
    t.right(11)
    t.forward(7)
t.hideturtle()
turtle.done()
