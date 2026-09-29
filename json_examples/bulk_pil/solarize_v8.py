"""{title}
Pillow 图像处理示例。{desc}
运行后在当前目录生成 'pil_solarize_v8'_preview.png。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

base = Image.new("RGB", (588, 384), "#20242c")
dr = ImageDraw.Draw(base)
for i in range(7):
    x0 = 20 + i * (588 - 60) // 7
dr.rectangle([588 // 2 - 70, 384 // 2, 588 // 2 + 70, 384 - 30], outline="#e8e8e8", width=3)

result = ImageOps.solarize(base, threshold=7 * 30 + 90)
result.save("pil_solarize_v8_preview.png")
print("已生成 pil_solarize_v8_preview.png")
