"""递归分形树·石墨·v8
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(39)
    tree(length * 0.82, depth - 1)
    t.right(39 * 2)
    tree(length * 0.82, depth - 1)
    t.left(39)
    t.backward(length)

tree(136, 8)
t.hideturtle()
turtle.done()
