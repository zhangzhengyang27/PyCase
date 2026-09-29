from PIL import Image, ImageDraw
"""验证码生成器：随机字符 + 干扰线 + 噪点"""
from PIL import Image, ImageDraw, ImageFont
import random
import string

W, H = 180, 60
chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

img = Image.new("RGB", (W, H), (245, 245, 245))
d = ImageDraw.Draw(img)

# 背景噪点
for _ in range(120):
    x, y = random.randint(0, W), random.randint(0, H)
    d.point((x, y), fill=(random.randint(120, 220),) * 3)

# 干扰线
for _ in range(4):
    d.line([(random.randint(0, W), random.randint(0, H)),
            (random.randint(0, W), random.randint(0, H))],
           fill=(random.randint(80, 200),) * 3, width=1)

# 字符（旋转）
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 32)
except Exception:
    font = ImageFont.load_default()
for i, c in enumerate(chars):
    layer = Image.new("RGBA", (40, 50), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((4, 6), c, font=font, fill=(random.randint(0, 120), random.randint(0, 120), random.randint(0, 150)))
    layer = layer.rotate(random.randint(-25, 25), expand=True, resample=Image.Resampling.BICUBIC)
    img.paste(layer, (10 + i * 42, 8), layer)

print("验证码:", chars)
img.save("captcha_demo.png")
print("已保存 captcha_demo.png")