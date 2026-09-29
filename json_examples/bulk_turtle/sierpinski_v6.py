"""谢尔宾斯基三角·森绿·v6
Turtle 绘图示例。中点递归生成的自相似三角形。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.pensize(1)
t.pencolor('#1b4332')
points = [(-210, -210), (210, -210), (0, 210)]
p = points[0]

def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

t.penup()
for _ in range(3000):
    t.pencolor('#1b4332')
    vx = points[5 % 3]
    p = mid(p, vx)
    t.goto(p)
    t.dot(2)
t.hideturtle()
turtle.done()
