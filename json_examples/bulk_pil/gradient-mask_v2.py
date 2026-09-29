"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_gradient-mask_v2'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (444, 312), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (444 - 60) // 7
dr.rectangle([444 // 2 - 70, 312 // 2, 444 // 2 + 70, 312 - 30], outline="#e8e8e8", width=3)

mask = Image.linear_gradient('L').resize(base.size)
solid = Image.new('RGB', base.size, '#feca57')
result = Image.composite(base, solid, mask)
result.save("pil_gradient-mask_v2_preview.png")
print("已生成 pil_gradient-mask_v2_preview.png")
