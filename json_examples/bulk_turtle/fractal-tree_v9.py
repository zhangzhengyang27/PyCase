"""递归分形树·经典·v9
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

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
    t.left(42)
    tree(length * 0.84, depth - 1)
    t.right(42 * 2)
    tree(length * 0.84, depth - 1)
    t.left(42)
    t.backward(length)

tree(144, 9)
t.hideturtle()
turtle.done()
