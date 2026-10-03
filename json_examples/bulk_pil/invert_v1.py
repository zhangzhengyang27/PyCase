"""反色·变体1
Pillow 图像处理示例。ImageOps.invert 颜色反转。（参数组 1）。
运行后在当前目录生成 'pil_invert_v1'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (420, 300), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (420 - 60) // 7
dr.rectangle([420 // 2 - 70, 300 // 2, 420 // 2 + 70, 300 - 30], outline="#e8e8e8", width=3)

result = ImageOps.invert(base)
result.save("pil_invert_v1_preview.png")
print("已生成 pil_invert_v1_preview.png")
