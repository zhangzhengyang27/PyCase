"""彩色螺旋线
Turtle 图形：用循环改变边长与颜色绘制渐变螺旋，演示 turtle 基本循环绘图。
运行后弹出画布窗口，绘制完成后点击窗口关闭。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor("black")
colors = ["red", "orange", "yellow", "green", "cyan", "purple"]

for i in range(120):
    t.pencolor(colors[i % 6])
    t.width(i // 20 + 1)
    t.forward(i * 2)
    t.left(59)

t.hideturtle()
turtle.done()
