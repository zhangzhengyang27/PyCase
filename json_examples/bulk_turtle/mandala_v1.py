"""对称曼陀罗·经典·v1
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']

def petal():
    for _ in range(5):
        t.forward(40)
        t.right(60)

for ring in range(5):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(10):
        petal()
        t.right(360 // 10)
    t.right(10)
    t.forward(6)
t.hideturtle()
turtle.done()
