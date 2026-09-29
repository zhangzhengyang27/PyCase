"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_invert_v4'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (492, 336), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (492 - 60) // 7
dr.rectangle([492 // 2 - 70, 336 // 2, 492 // 2 + 70, 336 - 30], outline="#e8e8e8", width=3)

result = ImageOps.invert(base)
result.save("pil_invert_v4_preview.png")
print("已生成 pil_invert_v4_preview.png")
