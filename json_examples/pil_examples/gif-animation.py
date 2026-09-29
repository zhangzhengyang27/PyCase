from PIL import Image, ImageDraw
"""GIF 动画生成：旋转渐变圆"""
from PIL import Image, ImageDraw
import math

W, H = 200, 200
frames = []
for angle in range(0, 360, 15):
    frame = Image.new("RGB", (W, H), (20, 20, 40))
    d = ImageDraw.Draw(frame)
    # 彩色扇区
    for i in range(8):
        a0 = math.radians(angle + i * 45)
        a1 = math.radians(angle + (i + 1) * 45)
        color = [(255, 60, 60), (255, 170, 40), (255, 240, 60), (120, 230, 80),
                 (60, 200, 200), (80, 130, 255), (170, 90, 255), (255, 100, 200)][i]
        d.pieslice([30, 30, 170, 170], a0, a1, fill=color)
    d.ellipse([78, 78, 122, 122], fill=(20, 20, 40))
    frames.append(frame)

frames[0].save("rotation_demo.gif", save_all=True, append_images=frames[1:],
               duration=90, loop=0)
print("已保存 rotation_demo.gif，共", len(frames), "帧")