"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_gaussian_v9'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (612, 396), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (612 - 60) // 7
dr.rectangle([612 // 2 - 70, 396 // 2, 612 // 2 + 70, 396 - 30], outline="#e8e8e8", width=3)

result = base.filter(ImageFilter.GaussianBlur(radius=8 + 1))
result.save("pil_gaussian_v9_preview.png")
print("已生成 pil_gaussian_v9_preview.png")
