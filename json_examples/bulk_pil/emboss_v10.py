"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_emboss_v10'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (636, 408), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (636 - 60) // 7
dr.rectangle([636 // 2 - 70, 408 // 2, 636 // 2 + 70, 408 - 30], outline="#e8e8e8", width=3)

result = base.filter(ImageFilter.EMBOSS)
result.save("pil_emboss_v10_preview.png")
print("已生成 pil_emboss_v10_preview.png")
