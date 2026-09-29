"""递归分形树·樱粉·v7
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#ff8fab', '#ffc2d1', '#ffe5ec', '#fb6f92', '#ffc9de']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(36)
    tree(length * 0.8, depth - 1)
    t.right(36 * 2)
    tree(length * 0.8, depth - 1)
    t.left(36)
    t.backward(length)

tree(128, 7)
t.hideturtle()
turtle.done()
