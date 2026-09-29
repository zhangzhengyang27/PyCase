"""递归分形树·经典·v1
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(18)
    tree(length * 0.68, depth - 1)
    t.right(18 * 2)
    tree(length * 0.68, depth - 1)
    t.left(18)
    t.backward(length)

tree(80, 7)
t.hideturtle()
turtle.done()
