"""龙曲线·暮色·v13
Turtle 绘图示例。纸带折叠序列生成的分形龙。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

turtle.bgcolor("#101418")
t = turtle.Turtle()
t.speed(0)
t.pensize(1)
t.pencolor('#edf2f4')
seq = [1]
for _ in range(8):
    seq = seq + [1] + [1 - s for s in reversed(seq)]
for step in seq:
    t.forward(5)
    t.right(90 if step else -90)
t.hideturtle()
turtle.done()
