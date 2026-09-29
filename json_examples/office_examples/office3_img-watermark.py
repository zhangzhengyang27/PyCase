"""批量水印：右下角半透明文字。"""
from PIL import Image, ImageDraw, ImageFont

base = Image.new("RGB", (640, 420), "#2b3a55")
d = ImageDraw.Draw(base)
for x in range(0, 640, 80):
    d.line([(x, 0), (x, 420)], fill="#3b4a66", width=1)

watermark = Image.new("RGBA", base.size, (0, 0, 0, 0))
wd = ImageDraw.Draw(watermark)
for y in range(20, 420, 90):
    for x in range(20, 640, 200):
        wd.text((x, y), "© 示例库", fill=(255, 255, 255, 90))
result = Image.alpha_composite(base.convert("RGBA"), watermark).convert("RGB")
result.save("水印图.png")
print("已生成 水印图.png")
