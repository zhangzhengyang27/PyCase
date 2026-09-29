"""递归分形树·薄荷·v4
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#80ffdb', '#72efdd', '#64dfdf', '#48bfe3', '#5390d9']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(27)
    tree(length * 0.74, depth - 1)
    t.right(27 * 2)
    tree(length * 0.74, depth - 1)
    t.left(27)
    t.backward(length)

tree(104, 7)
t.hideturtle()
turtle.done()
