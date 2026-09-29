"""对称曼陀罗·暮色·v5
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']

def petal():
    for _ in range(5):
        t.forward(64)
        t.right(76)

for ring in range(6):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(10):
        petal()
        t.right(360 // 10)
    t.right(14)
    t.forward(10)
t.hideturtle()
turtle.done()
