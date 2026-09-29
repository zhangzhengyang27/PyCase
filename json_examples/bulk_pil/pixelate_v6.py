"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_pixelate_v6'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (540, 360), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (540 - 60) // 7
dr.rectangle([540 // 2 - 70, 360 // 2, 540 // 2 + 70, 360 - 30], outline="#e8e8e8", width=3)

small = base.resize((base.width // 5 - 6, base.height // 5 - 8))
result = small.resize(base.size, Image.NEAREST)
result.save("pil_pixelate_v6_preview.png")
print("已生成 pil_pixelate_v6_preview.png")
