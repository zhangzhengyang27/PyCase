"""递归分形树·森绿·v6
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#1b4332', '#2d6a4f', '#40916c', '#74c69d', '#b7e4c7']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(33)
    tree(length * 0.78, depth - 1)
    t.right(33 * 2)
    tree(length * 0.78, depth - 1)
    t.left(33)
    t.backward(length)

tree(120, 9)
t.hideturtle()
turtle.done()
