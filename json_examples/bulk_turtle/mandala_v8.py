"""对称曼陀罗·石墨·v8
Turtle 绘图示例。外层旋转复制内层花纹的多重对称图案。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']

def petal():
    for _ in range(8):
        t.forward(82)
        t.right(88)

for ring in range(6):
    t.pencolor(colors[ring % len(colors)])
    for _ in range(13):
        petal()
        t.right(360 // 13)
    t.right(17)
    t.forward(13)
t.hideturtle()
turtle.done()
