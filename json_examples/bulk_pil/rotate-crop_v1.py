"""旋转裁剪·变体1
Pillow 图像处理示例。旋转 45 度后中心裁剪。（参数组 1）。
运行后在当前目录生成 'pil_rotate-crop_v1'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (420, 300), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (420 - 60) // 7
dr.rectangle([420 // 2 - 70, 300 // 2, 420 // 2 + 70, 300 - 30], outline="#e8e8e8", width=3)

rotated = base.rotate(45, expand=True, fillcolor='#111')
w, h = rotated.size
result = rotated.crop(((w - base.width) // 2, (h - base.height) // 2,
                       (w + base.width) // 2, (h + base.height) // 2))
result.save("pil_rotate-crop_v1_preview.png")
print("已生成 pil_rotate-crop_v1_preview.png")
