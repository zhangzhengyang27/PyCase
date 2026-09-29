"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_enhance-quad_v5'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (516, 348), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (516 - 60) // 7
dr.rectangle([516 // 2 - 70, 348 // 2, 516 // 2 + 70, 348 - 30], outline="#e8e8e8", width=3)

w, h = base.size
result = Image.new('RGB', (w * 2 + 8, h * 2 + 8), '#111')
for idx, im in enumerate([base, base.filter(ImageFilter.SHARPEN),
                          base.filter(ImageFilter.SMOOTH_MORE), base.filter(ImageFilter.FIND_EDGES)]):
    result.paste(im, ((idx % 2) * (w + 8), (idx // 2) * (h + 8)))
result.save("pil_enhance-quad_v5_preview.png")
print("已生成 pil_enhance-quad_v5_preview.png")
