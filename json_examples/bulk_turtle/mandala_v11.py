"""对称曼陀罗·暖阳·v11
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']

def petal():
    for _ in range(7):
        t.forward(100)
        t.right(100)

for ring in range(6):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(12):
        petal()
        t.right(360 // 12)
    t.right(20)
    t.forward(16)
t.hideturtle()
turtle.done()
