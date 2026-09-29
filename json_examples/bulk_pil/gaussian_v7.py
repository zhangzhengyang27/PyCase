"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_gaussian_v7'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (564, 372), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (564 - 60) // 7
dr.rectangle([564 // 2 - 70, 372 // 2, 564 // 2 + 70, 372 - 30], outline="#e8e8e8", width=3)

result = base.filter(ImageFilter.GaussianBlur(radius=6 + 1))
result.save("pil_gaussian_v7_preview.png")
print("已生成 pil_gaussian_v7_preview.png")
