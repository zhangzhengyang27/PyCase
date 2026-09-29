"""渐变螺旋·石墨·v8
Turtle 绘图示例。边长递增的螺旋线，按取模轮换色板颜色。
运行后弹出画布，绘制完成自动退出事件循环。
"""
import turtle

t = turtle.Turtle()
t.speed(0)
colors = ['#212529', '#495057', '#868e96', '#ced4da', '#f8f9fa']
for i in range(240):
    t.pencolor(colors[i % len(colors)])
    t.width(1 + i // 22)
    t.forward(i * 4.800000000000001)
    t.left(76)
t.hideturtle()
turtle.done()
