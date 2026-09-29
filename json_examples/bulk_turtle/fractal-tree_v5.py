"""递归分形树·暮色·v5
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

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
    t.left(30)
    tree(length * 0.76, depth - 1)
    t.right(30 * 2)
    tree(length * 0.76, depth - 1)
    t.left(30)
    t.backward(length)

tree(112, 8)
t.hideturtle()
turtle.done()
