"""科赫雪花·暮色·v5
Turtle 绘图示例。科赫曲线三连成雪花，迭代深度决定细节层级。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.pensize(2)
t.pencolor('#d90429')

def koch(length, depth):
    if depth == 0:
        t.forward(length)
        return
    length /= 3
    koch(length, depth - 1)
    t.left(60)
    koch(length, depth - 1)
    t.right(120)
    koch(length, depth - 1)
    t.left(60)
    koch(length, depth - 1)

for _ in range(3):
    koch(260, 3)
    t.right(120)
t.hideturtle()
turtle.done()
