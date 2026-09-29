"""{title}
Turtle 图形：{desc}
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("black")
colors = ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#f368e0"]


def petal():
    for _ in range(6):
        t.forward(60)
        t.right(60)
    t.forward(30)


for ring in range(6):
    t.pencolor(colors[ring % 5])
    for _ in range(12):
        petal()
        t.right(30)
    t.right(10)
    t.forward(8)

t.hideturtle()
turtle.done()
