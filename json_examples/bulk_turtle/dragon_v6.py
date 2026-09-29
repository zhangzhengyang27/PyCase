"""龙曲线·森绿·v6
Turtle 绘图示例。纸带折叠序列生成的分形龙。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.pencolor('#1b4332')
seq = [1]
for _ in range(9):
    seq = seq + [1] + [1 - s for s in reversed(seq)]
for step in seq:
    t.forward(7)
    t.right(90 if step else -90)
t.hideturtle()
turtle.done()
