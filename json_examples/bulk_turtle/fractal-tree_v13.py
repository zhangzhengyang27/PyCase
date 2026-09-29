"""递归分形树·暮色·v13
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(54)
    tree(length * 0.92, depth - 1)
    t.right(54 * 2)
    tree(length * 0.92, depth - 1)
    t.left(54)
    t.backward(length)

tree(176, 7)
t.hideturtle()
turtle.done()
