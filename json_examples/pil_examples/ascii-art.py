from PIL import Image, ImageDraw
"""ASCII 艺术：图像亮度 → 字符画"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 程序化生成爱心图案
W, H = 120, 60
img = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(img)
for i in range(1, 24, 2):
    d.arc([(W // 2 - i * 3, H // 2 - i * 2), (W // 2 + i * 3, H // 2 + i * 2)],
          start=0, end=180, fill=255 - i * 10)
    d.arc([(W // 2 - i * 3, H // 2 - i * 2), (W // 2 + i * 3, H // 2 + i * 2)],
          start=180, end=360, fill=255 - i * 10)

# 缩到字符画分辨率
small = img.resize((64, 32))
gray = np.asarray(small)

chars = " .:-=+*#%@"
out_lines = []
for row in gray:
    line = "".join(chars[min(len(chars) - 1, int(v) * (len(chars) - 1) // 255)] for v in row)
    out_lines.append(line)
print("\n".join(out_lines))
# 将字符画渲染为图片（供前端预览）
_img = Image.new("RGB", (64 * 9, 32 * 17), "white")
_draw = ImageDraw.Draw(_img)
try:
    _font = ImageFont.load_default(size=16)
except TypeError:
    _font = ImageFont.load_default()
for _y, _line in enumerate(out_lines):
    _draw.text((4, _y * 16), _line, fill="black", font=_font)
_img.save("ascii_demo.png")
print("[输出] 字符画图片已保存: ascii_demo.png")
