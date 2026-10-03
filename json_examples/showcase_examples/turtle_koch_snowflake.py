"""科赫雪花
Turtle 图形：经典分形：三段科赫曲线组成雪花，观察迭代次数与复杂度的关系。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.pensize(2)
t.pencolor("#1e6fd9")


def koch(length: float, depth: int):
    if depth == 0:
        t.forward(length)
        return
    length /= 3
    koch(length, depth - 1)
    t.left(60)
    koch(length, depth - 1)
    t.right(120)
    koch(length, depth - 1)
    t.left(60)
    koch(length, depth - 1)


for _ in range(3):
    koch(240, 3)
    t.right(120)

t.hideturtle()
turtle.done()
