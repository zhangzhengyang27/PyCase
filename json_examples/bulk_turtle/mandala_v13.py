"""对称曼陀罗·暮色·v13
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']

def petal():
    for _ in range(5):
        t.forward(112)
        t.right(108)

for ring in range(5):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(10):
        petal()
        t.right(360 // 10)
    t.right(22)
    t.forward(18)
t.hideturtle()
turtle.done()
