"""递归分形树·暖阳·v11
Turtle 绘图示例。二叉分形树，递归深度与分支角度决定形态。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.left(90)
colors = ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff']

def tree(length, depth):
    if depth == 0:
        return
    t.width(depth)
    t.pencolor(colors[depth % len(colors)])
    t.forward(length)
    t.left(48)
    tree(length * 0.88, depth - 1)
    t.right(48 * 2)
    tree(length * 0.88, depth - 1)
    t.left(48)
    t.backward(length)

tree(160, 8)
t.hideturtle()
turtle.done()
