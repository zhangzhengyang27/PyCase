"""递归分形树·海雾·v10
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#0b3954', '#087e8b', '#bfd7ea', '#ff5a5f', '#c81d25']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(45)
    tree(length * 0.86, depth - 1)
    t.right(45 * 2)
    tree(length * 0.86, depth - 1)
    t.left(45)
    t.backward(length)

tree(152, 7)
t.hideturtle()
turtle.done()
