"""对称曼陀罗·森绿·v6
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']

def petal():
    for _ in range(6):
        t.forward(70)
        t.right(80)

for ring in range(7):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(11):
        petal()
        t.right(360 // 11)
    t.right(15)
    t.forward(11)
t.hideturtle()
turtle.done()
