"""递归分形树
Turtle 图形：递归绘制二叉分形树，随深度改变枝干粗细与颜色，理解递归图形。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

t = turtle.Turtle()
t.left(90)
t.speed(0)


def tree(length: float, depth: int):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor("brown" if depth > 3 else "green")
    t.forward(length)
    t.left(25)
    tree(length * 0.72, depth - 1)
    t.right(50)
    tree(length * 0.72, depth - 1)
    t.left(25)
    t.backward(length)


tree(90, 8)
t.hideturtle()
turtle.done()
