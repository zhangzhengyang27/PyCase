"""谢尔宾斯基三角·暮色·v13
Turtle 绘图示例。中点递归生成的自相似三角形。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
t.pencolor('#edf2f4')
points = [(-280, -280), (280, -280), (0, 280)]
p = points[0]

def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

t.penup()
for _ in range(5100):
    t.pencolor('#edf2f4')
    vx = points[12 % 3]
    p = mid(p, vx)
    t.goto(p)
    t.dot(2)
t.hideturtle()
turtle.done()
