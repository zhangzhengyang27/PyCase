"""对称曼陀罗·薄荷·v4
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']

def petal():
    for _ in range(8):
        t.forward(58)
        t.right(72)

for ring in range(5):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(13):
        petal()
        t.right(360 // 13)
    t.right(13)
    t.forward(9)
t.hideturtle()
turtle.done()
