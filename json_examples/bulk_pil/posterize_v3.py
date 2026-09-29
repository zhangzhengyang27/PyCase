"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_posterize_v3'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (468, 324), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (468 - 60) // 7
dr.rectangle([468 // 2 - 70, 324 // 2, 468 // 2 + 70, 324 - 30], outline="#e8e8e8", width=3)

result = ImageOps.posterize(base, bits=2 + 2)
result.save("pil_posterize_v3_preview.png")
print("已生成 pil_posterize_v3_preview.png")
