"""镜像拼贴·变体1
Pillow 图像处理示例。水平镜像后与原图并排。（参数组 1）。
运行后在当前目录生成 'pil_mirror_v1'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (420, 300), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (420 - 60) // 7
dr.rectangle([420 // 2 - 70, 300 // 2, 420 // 2 + 70, 300 - 30], outline="#e8e8e8", width=3)

result = Image.new('RGB', (base.width * 2, base.height))
result.paste(base, (0, 0))
result.paste(ImageOps.mirror(base), (base.width, 0))
result.save("pil_mirror_v1_preview.png")
print("已生成 pil_mirror_v1_preview.png")
