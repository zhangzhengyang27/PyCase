"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_rotate-crop_v5'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (516, 348), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (516 - 60) // 7
dr.rectangle([516 // 2 - 70, 348 // 2, 516 // 2 + 70, 348 - 30], outline="#e8e8e8", width=3)

rotated = base.rotate(45, expand=True, fillcolor='#111')
w, h = rotated.size
result = rotated.crop(((w - base.width) // 2, (h - base.height) // 2,
                       (w + base.width) // 2, (h + base.height) // 2))
result.save("pil_rotate-crop_v5_preview.png")
print("已生成 pil_rotate-crop_v5_preview.png")
