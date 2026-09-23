# -*- coding: utf-8 -*-
"""生成 PIL 图像处理示例集合 pil_examples.json。
所有示例数据自包含：素材图由 Pillow 程序化生成（渐变/棋盘/图形/噪声），不依赖外部图片文件。
功能覆盖参考 Pillow 官方 Tutorial / Handbook、XavierJiezou/Python-Pillow-Tutorial、
BetulKarakaya/Learn-Image-Processing-With-Me 等开源资源。
"""
import json
import os

# matplotlib 中文字体配置片段（PIL 示例用 plt 显示图片时注入）
FONT_HELPER = '''# 尝试设置中文字体（找不到时中文显示为方块但不影响运行）
try:
    from matplotlib import font_manager
    _zh_fonts = [f.name for f in font_manager.fontManager.ttflist if any(
        k in f.name for k in ("PingFang", "Heiti", "Songti", "Hiragino", "YaHei", "SimHei", "Arial Unicode"))]
    if _zh_fonts:
        plt.rcParams["font.sans-serif"] = [_zh_fonts[0]]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass
'''

EXAMPLES = []

# 元数据覆盖层：标题/描述/tag 统一为数据可视化风格
# （title 名词短语、tags 两个词 [类型, 特性]、description "内容，演示/对比 XX"）
META_OVERRIDES = {
    'gradient-generator.py': {
        'title': 'RGB 渐变图',
        'tags': ['图像生成', '渐变'],
        'description': '水平/垂直/对角三向 RGB 渐变图，演示 Pillow 从零创建图像与像素写入。'},
    'resize-thumbnail.py': {
        'title': '缩放与缩略图',
        'tags': ['缩放', '重采样'],
        'description': '棋盘图用最近邻、双线性、双三次算法缩放并生成缩略图，对比插值效果差异。'},
    'crop-paste.py': {
        'title': '裁剪与粘贴合成',
        'tags': ['裁剪', '合成'],
        'description': '拼色图案的裁剪、旋转与多图粘贴拼接，演示 crop、paste 与画布合成。'},
    'rotate-flip.py': {
        'title': '旋转与翻转',
        'tags': ['旋转', '翻转'],
        'description': '方向图多角度旋转与水平/垂直翻转对比，演示 rotate 的 expand 扩展画布用法。'},
    'grayscale-sepia.py': {
        'title': '灰度与老照片效果',
        'tags': ['灰度', '复古'],
        'description': '彩色风景图的灰度转换与棕褐色老照片风格处理，演示 L 模式转换与像素运算。'},
    'color-channels.py': {
        'title': 'RGB 通道分离',
        'tags': ['色彩', '通道'],
        'description': '三色圆分离出 R/G/B 单通道并分别染色显示，演示通道拆分与合并。'},
    'pixel-art.py': {
        'title': '像素风马赛克',
        'tags': ['特效', '像素风'],
        'description': '渐变圆降采样后最近邻放大形成像素风，演示重采样与低分辨率艺术效果。'},
    'point-operations.py': {
        'title': '点运算与均衡化',
        'tags': ['色彩', '点运算'],
        'description': '反色、自动对比度、直方图均衡化与色调分离的效果对比，演示 ImageOps 点运算。'},
    'filter-gallery.py': {
        'title': '内置滤镜效果画廊',
        'tags': ['滤镜', '效果'],
        'description': '同一图像应用模糊、轮廓、浮雕、锐化等 8 种内置滤镜，直观对比滤镜效果。'},
    'custom-kernel.py': {
        'title': '自定义卷积核滤镜',
        'tags': ['滤镜', '卷积'],
        'description': '3x3 卷积核实现锐化、浮雕与高斯模糊，演示 ImageFilter.Kernel 自定义滤波。'},
    'edge-detect.py': {
        'title': '边缘检测流水线',
        'tags': ['滤镜', '边缘检测'],
        'description': '高斯降噪、查找边缘与自动对比度增强的处理流程，提取图像轮廓。'},
    'draw-shapes.py': {
        'title': 'ImageDraw 几何绘制',
        'tags': ['绘制', '几何'],
        'description': '线条、矩形、椭圆、圆弧、扇形与多边形的综合绘制，覆盖 ImageDraw 基础 API。'},
    'draw-text-watermark.py': {
        'title': '文字与水印',
        'tags': ['文字', '水印'],
        'description': '图中文字与半透明平铺水印的叠加，演示 ImageFont 与 RGBA 合成。'},
    'captcha-generator.py': {
        'title': '验证码生成',
        'tags': ['验证码', '随机'],
        'description': '随机字符、旋转、干扰线与噪点组合的验证码图片，演示综合绘图应用。'},
    'image-blend.py': {
        'title': '图像融合渐变',
        'tags': ['合成', '融合'],
        'description': '两张图像按 0 到 1 的权重梯度融合，演示 Image.blend 过渡效果。'},
    'paste-mask.py': {
        'title': '蒙版粘贴合成',
        'tags': ['合成', '蒙版'],
        'description': '径向渐变蒙版让前景图与星空底图无缝融合，演示 paste 的 mask 用法。'},
    'ascii-art.py': {
        'title': 'ASCII 字符画',
        'tags': ['特效', '字符画'],
        'description': '图像亮度映射为字符集输出控制台字符画，演示像素读取与字符可视化。'},
    'vintage-filter.py': {
        'title': '复古滤镜与暗角',
        'tags': ['特效', '复古'],
        'description': '棕褐色调、四周暗角与胶片噪点的组合处理，实现老照片风格滤镜。'},
    'glow-effect.py': {
        'title': '霓虹发光效果',
        'tags': ['特效', '发光'],
        'description': '边缘提取与多层高斯模糊叠加的发光特效，模拟霓虹灯管效果。'},
    'gif-animation.py': {
        'title': 'GIF 动画生成',
        'tags': ['GIF', '动画'],
        'description': '多帧旋转渐变圆合成动态 GIF，演示 save_all 与 append_images 动画制作。'},
    'histogram-equalize.py': {
        'title': '直方图与均衡化',
        'tags': ['直方图', '增强'],
        'description': '低对比度图像的直方图分析与均衡化前后对比，提升图像对比度。'},
    'nine-grid-split.py': {
        'title': '九宫格切图',
        'tags': ['裁剪', '切片'],
        'description': '图像按 3x3 均匀切分为九张子图，演示 crop 批量切片。'},
    'image-diff.py': {
        'title': '图像差异检测',
        'tags': ['差异检测', '比对'],
        'description': '两张相似图像用像素差找出差异区域并高亮框出，演示 ImageChops 比对。'},
    'collage-grid.py': {
        'title': '缩略图墙',
        'tags': ['拼接', '批量'],
        'description': '多张缩略图按 2x3 网格拼成拼图墙，演示批量处理与拼接。'},
}

# 每个示例中"绘制器变量 -> 绘制目标图像变量"映射（用于修复 __import__ 拿模块而非实例的问题）
DRAW_TARGETS = {
    'resize-thumbnail.py': [('d', 'img')],
    'crop-paste.py': [('d', 'yellow'), ('d2', 'cyan')],
    'rotate-flip.py': [('d', 'img')],
    'grayscale-sepia.py': [('d', 'sun')],
    'color-channels.py': [('d', 'img')],
    'point-operations.py': [('d', 'low')],
    'filter-gallery.py': [('d', 'bg')],
    'custom-kernel.py': [('d', 'img')],
    'edge-detect.py': [('d', 'img')],
    'image-blend.py': [('d1', 'img1'), ('d2', 'img2')],
    'paste-mask.py': [('d', 'bg'), ('fd', 'fg')],
    'ascii-art.py': [('d', 'img')],
    'vintage-filter.py': [('d', 'img')],
    'glow-effect.py': [('d', 'img')],
    'histogram-equalize.py': [('d', 'img')],
    'nine-grid-split.py': [('d', 'img')],
    'image-diff.py': [('d', 'base'), ('d2', 'img2'), ('md', 'mark')],
    'collage-grid.py': [('d', 'img')],
}


def fix_draw(name, code):
    """把 __import__ 拿模块的写法修复为 ImageDraw.Draw(实例)，并补顶部导入"""
    for var, target in DRAW_TARGETS.get(name, []):
        code = code.replace(
            f'{var} = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw',
            f'{var} = ImageDraw.Draw({target})')
    if "= ImageDraw.Draw(" in code and "import ImageDraw" not in code:
        # 在首个 PIL import 行追加 ImageDraw
        for pil_line in ["from PIL import Image, ImageOps\n", "from PIL import Image\n"]:
            if pil_line in code:
                code = code.replace(pil_line, pil_line.replace("import Image", "import Image, ImageDraw", 1).replace("import ImageOps, ImageDraw", "import ImageOps, ImageDraw", 1), 1)
                break
        else:
            code = "from PIL import Image, ImageDraw\n" + code
    return code


def _ensure_image_output(name, code):
    """确保每个示例都会在运行目录落盘一张图片，供 sidecar 扫描后前端预览。"""
    stem = name[:-3]
    # 有 matplotlib 展示块的：在 close 前 savefig 保存拼图
    if "plt.close('all')" in code:
        code = code.replace(
            "plt.close('all')",
            f'plt.savefig("{stem}_preview.png", bbox_inches="tight", dpi=110)\nplt.close("all")',
        )
    # 特判：ASCII 字符画把文本渲染成图片
    if name == "ascii-art.py":
        code = code.replace(
            "from PIL import Image\n",
            "from PIL import Image, ImageDraw, ImageFont\n", 1,
        )
        code += '''
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
'''
    return code


def add(name, title, description, tags, code):
    """构造并登记一个示例（元数据可由 META_OVERRIDES 覆盖）"""
    ov = META_OVERRIDES.get(name)
    if ov:
        title, description, tags = ov["title"], ov["description"], ov["tags"]
    code = code.strip()
    # 去掉 plt.show()（运行环境无交互窗口，会阻塞子进程）；
    # 图片改为保存到工作目录，由 sidecar 扫描后在前端输出区预览。
    code = code.replace("plt.show()", "plt.close('all')")
    code = _ensure_image_output(name, code)
    if "import matplotlib.pyplot as plt" in code and "font_manager" not in code:
        code = code.replace("import matplotlib.pyplot as plt",
                            "import matplotlib.pyplot as plt\n" + FONT_HELPER, 1)
    code = fix_draw(name, code)
    EXAMPLES.append({
        "id": f"topics_python-basics_pillow-{name}",
        "name": name,
        "category": "topics",
        "tags": tags,
        "title": title,
        "description": description,
        "requirements": ["pillow", "numpy", "matplotlib"],
        "code": code,
    })


# 1. 渐变图像生成
add(
    "gradient-generator.py", "渐变图像生成器",
    "程序化生成水平/垂直/对角 RGB 渐变图，演示 Pillow 从零创建图像（putdata/像素写入）。",
    ["图像生成", "基础"],
    '''
"""渐变图像生成器：程序化创建 RGB 渐变图"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

W, H = 400, 300

# 水平渐变：R 从左到右 0->255
x = np.linspace(0, 255, W, dtype=np.uint8)
horiz = np.tile(x, (H, 1))

# 垂直渐变：G 从上到下 0->255
y = np.linspace(0, 255, H, dtype=np.uint8).reshape(-1, 1)
vert = np.tile(y, (1, W))

# 对角渐变：B 从 (0,0) 到 (W,H)
diag = np.linspace(0, 255, W + H, dtype=np.uint8)
diag_map = np.array([[diag[i + j] for j in range(W)] for i in range(H)])

rgb = np.stack([horiz, vert, diag_map], axis=-1).astype(np.uint8)
img = Image.fromarray(rgb, "RGB")

plt.figure(figsize=(8, 6))
plt.imshow(img)
plt.axis("off")
plt.title("RGB 渐变图：R 水平 / G 垂直 / B 对角")
plt.show()
img.save("gradient_demo.png")
print("已保存 gradient_demo.png")
''')

# 2. 缩放与缩略图
add(
    "resize-thumbnail.py", "缩放与缩略图",
    "程序化生成棋盘图后，用不同重采样算法缩放并生成缩略图，对比插值效果。",
    ["缩放", "基础"],
    '''
"""缩放与缩略图：不同重采样算法对比"""
from PIL import Image
import matplotlib.pyplot as plt

# 程序化生成 320x320 棋盘格
W = 320
img = Image.new("RGB", (W, W), "white")
d = ImageDraw.Draw(img)
for i in range(8):
    for j in range(8):
        if (i + j) % 2 == 0:
            d.rectangle([i * 40, j * 40, i * 40 + 40, j * 40 + 40], fill=(30, 144, 255))

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(img)
axes[0, 0].set_title("原图 320x320")
axes[0, 0].axis("off")

modes = [("最近邻", Image.Resampling.NEAREST), ("双线性", Image.Resampling.BILINEAR),
         ("双三次", Image.Resampling.BICUBIC)]
for ax, (label, mode) in zip(axes.flat[1:], modes):
    small = img.resize((100, 100), mode).resize((320, 320), mode)
    ax.imshow(small)
    ax.set_title(label)
    ax.axis("off")

plt.suptitle("缩放算法对比：先缩到 1/3 再放大回原尺寸")
plt.tight_layout()
plt.show()

thumb = img.copy()
thumb.thumbnail((96, 96))
print("缩略图尺寸:", thumb.size)
thumb.save("thumbnail_demo.png")
''')

# 3. 裁剪与粘贴合成
add(
    "crop-paste.py", "裁剪与粘贴合成",
    "程序化生成拼色图案，演示 crop 裁剪、paste 粘贴与 Image.new 画布合成。",
    ["裁剪", "合成"],
    '''
"""裁剪与粘贴合成：拼贴画效果"""
from PIL import Image
import matplotlib.pyplot as plt

# 生成 300x300 渐变底图
import numpy as np
xx = np.linspace(0, 255, 300, dtype=np.uint8)
base = Image.fromarray(np.tile(xx, (300, 1)).astype(np.uint8), "L").convert("RGB")

# 生成黄色圆
yellow = Image.new("RGB", (150, 150), "white")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([10, 10, 140, 140], fill=(255, 215, 0))
# 生成青色方块
cyan = Image.new("RGB", (150, 150), "white")
d2 = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d2.rectangle([30, 30, 120, 120], fill=(0, 200, 200))

# 裁剪渐变图左上 150x150
crop = base.crop((0, 0, 150, 150))

# 拼贴：底图 + 四角元素
canvas = Image.new("RGB", (450, 450), "lightgray")
canvas.paste(base, (0, 0))
canvas.paste(yellow, (150, 0))
canvas.paste(cyan, (300, 0))
canvas.paste(crop.rotate(180), (0, 150))
canvas.paste(crop.rotate(90), (150, 150))
canvas.paste(crop.rotate(270), (300, 150))

plt.figure(figsize=(8, 8))
plt.imshow(canvas)
plt.axis("off")
plt.title("裁剪与粘贴合成拼贴画")
plt.show()
canvas.save("crop_paste_demo.png")
''')

# 4. 旋转与翻转
add(
    "rotate-flip.py", "旋转与翻转",
    "程序化生成带箭头的方向图，演示 rotate（含 expand 扩展画布）与 transpose 翻转。",
    ["旋转", "翻转"],
    '''
"""旋转与翻转：方向图的多种变换"""
from PIL import Image
import matplotlib.pyplot as plt

# 生成 240x240 方向图：白底 + 蓝色箭头 + 红色圆点
img = Image.new("RGB", (240, 240), "white")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.polygon([(120, 20), (200, 100), (150, 100), (150, 220), (90, 220), (90, 100), (40, 100)], fill=(30, 144, 255))
d.ellipse([100, 100, 140, 140], fill=(255, 80, 80))

fig, axes = plt.subplots(2, 3, figsize=(12, 8))
titles = ["原图", "旋转 45°", "旋转 45°+扩展画布", "水平翻转", "垂直翻转", "旋转 90°"]
images = [img,
          img.rotate(45),
          img.rotate(45, expand=True),
          img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
          img.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
          img.transpose(Image.Transpose.ROTATE_90)]
for ax, t, im in zip(axes.flat, titles, images):
    ax.imshow(im)
    ax.set_title(t)
    ax.axis("off")
plt.suptitle("旋转与翻转：expand 会扩展画布适应新角度")
plt.tight_layout()
plt.show()
''')

# 5. 灰度化与棕褐色调
add(
    "grayscale-sepia.py", "灰度化与老照片",
    "程序化生成彩色风景色块图，演示灰度转换（L 模式）与棕褐色老照片风格（像素运算）。",
    ["色彩", "复古"],
    '''
"""灰度化与老照片：彩色图 → 灰度 → 棕褐色调"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成"风景"：天空渐变 + 绿色山丘 + 橙色太阳
W, H = 400, 300
sky = np.linspace(135, 206, H, dtype=np.uint8).reshape(-1, 1)
arr = np.zeros((H, W, 3), dtype=np.uint8)
arr[:, :, 0] = np.tile(sky, (1, W))
arr[:, :, 1] = 180
arr[:, :, 2] = 235
arr[H // 2:, :, 0] = 60
arr[H // 2:, :, 1] = 160
arr[H // 2:, :, 2] = 80
sun = Image.fromarray(arr, "RGB")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([150, 80, 250, 180], fill=(255, 160, 40))

gray = sun.convert("L")

# 棕褐色：L -> (R,G,B) = (L*1.05, L*0.87, L*0.58)
g = np.asarray(gray).astype(np.float32)
sepia = np.stack([g * 1.05, g * 0.87, g * 0.58], axis=-1)
sepia = np.clip(sepia, 0, 255).astype(np.uint8)
sepia = Image.fromarray(sepia)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, im, t in zip(axes, [sun, gray, sepia], ["原图", "灰度", "老照片棕褐"]):
    ax.imshow(im, cmap="gray" if im.mode == "L" else None)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.show()
''')

# 6. RGB 通道分离
add(
    "color-channels.py", "RGB 通道分离",
    "程序化生成三色圆后分离 R/G/B 通道，演示通道拆分与合并、单通道染色显示。",
    ["色彩", "通道"],
    '''
"""RGB 通道分离与合并"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成 300x300 三色圆
img = Image.new("RGB", (300, 300), "black")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([50, 50, 250, 250], fill=(255, 0, 0))
d.ellipse([80, 80, 220, 220], fill=(0, 255, 0))
d.ellipse([110, 110, 190, 190], fill=(0, 0, 255))

r, g, b = img.split()

# 把单通道染回对应颜色
def tint(channel, color):
    black = Image.new("RGB", channel.size, (0, 0, 0))
    black.paste(color, (0, 0), channel)
    return black

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(img)
axes[0, 0].set_title("原图")
axes[0, 1].imshow(tint(r, (255, 0, 0)))
axes[0, 1].set_title("R 通道")
axes[1, 0].imshow(tint(g, (0, 255, 0)))
axes[1, 0].set_title("G 通道")
axes[1, 1].imshow(tint(b, (0, 0, 255)))
axes[1, 1].set_title("B 通道")
for ax in axes.flat:
    ax.axis("off")
plt.tight_layout()
plt.show()
''')

# 7. 像素风马赛克
add(
    "pixel-art.py", "像素风马赛克",
    "生成渐变圆后降采样再最近邻放大，制造像素风（马赛克）效果，演示 Image.resize 重采样。",
    ["特效", "像素风"],
    '''
"""像素风马赛克：降采样 + 最近邻放大"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成 400x400 渐变圆
W = 400
xx, yy = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, W))
r = np.sqrt(xx ** 2 + yy ** 2)
hue = np.arctan2(yy, xx)
# HSV 转简易 RGB 彩虹圆
hsv = np.stack([(hue + np.pi) / (2 * np.pi), np.ones_like(r), 1 - r], axis=-1)
import colorsys
rgb = np.zeros((W, W, 3))
for i in range(0, W, 25):
    for j in range(0, W, 25):
        h, s, v = hsv[i, j]
        rgb[i:i + 25, j:j + 25] = colorsys.hsv_to_rgb(h, s, v)
img = Image.fromarray((rgb * 255).astype(np.uint8))

# 马赛克：先缩到 40x40 再放大回 400x400
pixel = img.resize((40, 40), Image.Resampling.NEAREST).resize((W, W), Image.Resampling.NEAREST)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(img)
axes[0].set_title("原图 400x400")
axes[0].axis("off")
axes[1].imshow(pixel)
axes[1].set_title("像素风 40x40 马赛克")
axes[1].axis("off")
plt.tight_layout()
plt.show()
''')

# 8. 点运算：反色/均衡/对比
add(
    "point-operations.py", "点运算与均衡化",
    "演示 ImageOps 的反色、自动对比度、均衡化与 posterize 色调分离，理解逐像素点运算。",
    ["色彩", "点运算"],
    '''
"""点运算：反色 / 自动对比度 / 直方图均衡化 / 色调分离"""
from PIL import Image, ImageOps
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成低对比度渐变图（模拟欠曝照片）
W, H = 300, 300
v = np.linspace(60, 120, W, dtype=np.uint8)  # 低动态范围
low = Image.fromarray(np.tile(v, (H, 1)), "L")
low = low.convert("RGB")

d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([80, 80, 220, 220], outline=(255, 255, 255), width=3)
d.line([(0, 150), (300, 150)], fill=(255, 255, 255), width=2)
d.line([(150, 0), (150, 300)], fill=(255, 255, 255), width=2)

results = {
    "原图": low,
    "反色 invert": ImageOps.invert(low),
    "自动对比度": ImageOps.autocontrast(low, cutoff=2),
    "直方图均衡": ImageOps.equalize(low),
    "色调分离 4 级": ImageOps.posterize(low, 4),
    "灰度化": low.convert("L"),
}

fig, axes = plt.subplots(2, 3, figsize=(13, 9))
for ax, (t, im) in zip(axes.flat, results.items()):
    ax.imshow(im, cmap="gray" if im.mode == "L" else None)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.show()
''')

# 9. 滤镜效果画廊
add(
    "filter-gallery.py", "滤镜效果画廊",
    "一个图像同时应用 8 种 Pillow 内置滤镜（模糊/轮廓/细节/浮雕/边缘/锐化等）对比展示。",
    ["滤镜", "画廊"],
    '''
"""滤镜效果画廊：8 种内置滤镜对比"""
from PIL import Image, ImageFilter
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成测试图：几何图形 + 渐变背景
W, H = 300, 300
xx = np.linspace(0, 255, W, dtype=np.uint8)
bg = Image.fromarray(np.tile(xx, (H, 1)), "L").convert("RGB")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([40, 40, 260, 260], fill=(255, 220, 100), outline=(255, 80, 80), width=6)
d.rectangle([90, 90, 210, 210], outline=(40, 120, 255), width=6)
d.line([(30, 270), (270, 30)], fill=(80, 200, 80), width=8)

filters = [
    ("原图", None),
    ("BLUR 模糊", ImageFilter.BLUR),
    ("CONTOUR 轮廓", ImageFilter.CONTOUR),
    ("DETAIL 细节", ImageFilter.DETAIL),
    ("EMBOSS 浮雕", ImageFilter.EMBOSS),
    ("EDGE_ENHANCE 边缘增强", ImageFilter.EDGE_ENHANCE),
    ("FIND_EDGES 查找边缘", ImageFilter.FIND_EDGES),
    ("SHARPEN 锐化", ImageFilter.SHARPEN),
    ("SMOOTH 平滑", ImageFilter.SMOOTH),
]

fig, axes = plt.subplots(3, 3, figsize=(12, 12))
for ax, (t, f) in zip(axes.flat, filters):
    im = bg.filter(f) if f else bg
    ax.imshow(im)
    ax.set_title(t, fontsize=10)
    ax.axis("off")
plt.suptitle("Pillow 内置滤镜效果")
plt.tight_layout()
plt.show()
''')

# 10. 自定义卷积核
add(
    "custom-kernel.py", "自定义卷积核滤镜",
    "用 ImageFilter.Kernel 自定义 3x3 卷积核实现锐化、浮雕、模糊，理解卷积滤波原理。",
    ["滤镜", "卷积"],
    '''
"""自定义卷积核：3x3 锐化 / 浮雕 / 模糊"""
from PIL import Image, ImageFilter
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成测试图
W, H = 280, 280
img = Image.new("RGB", (W, H), "white")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([40, 40, 240, 240], fill=(255, 170, 60), outline=(120, 60, 200), width=5)
for i in range(0, 280, 20):
    d.line([(i, 0), (i, 280)], fill=(200, 200, 220), width=1)
    d.line([(0, i), (280, i)], fill=(200, 200, 220), width=1)

kernels = [
    ("锐化", (0, -1, 0, -1, 5, -1, 0, -1, 0), 1.0),
    ("浮雕", (-1, -1, 0, -1, 0, 1, 0, 1, 1), 1.0),
    ("高斯模糊", (1, 2, 1, 2, 4, 2, 1, 2, 1), 16.0),
]

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(img)
axes[0, 0].set_title("原图")
axes[0, 0].axis("off")
for ax, (t, kern, scale) in zip(axes.flat[1:], kernels):
    out = img.filter(ImageFilter.Kernel((3, 3), kern, scale=scale, offset=128 if "浮雕" in t else 0))
    ax.imshow(out)
    ax.set_title(f"{t}（3x3 卷积核）")
    ax.axis("off")
plt.tight_layout()
plt.show()
''')

# 11. 边缘检测流水线
add(
    "edge-detect.py", "边缘检测流水线",
    "高斯模糊降噪 → 查找边缘 → 灰度增强，完整演示图像边缘提取处理流程。",
    ["滤镜", "边缘检测"],
    '''
"""边缘检测流水线：降噪 → 找边缘 → 增强"""
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成带噪点的几何图
W, H = 300, 300
img = Image.new("RGB", (W, H), (245, 245, 245))
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.rectangle([40, 40, 260, 260], outline=(40, 40, 40), width=4)
d.ellipse([90, 90, 210, 210], outline=(40, 40, 40), width=4)
d.line([(40, 260), (260, 40)], fill=(40, 40, 40), width=4)

# 加椒盐噪点
arr = np.asarray(img).copy()
rng = np.random.default_rng(7)
mask = rng.random((H, W)) < 0.03
arr[mask] = [0, 0, 0]
noisy = Image.fromarray(arr)

# 流水线
denoised = noisy.filter(ImageFilter.GaussianBlur(1.2))
edges = denoised.filter(ImageFilter.FIND_EDGES).convert("L")
edges_enhanced = ImageOps.autocontrast(edges)

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
for ax, im, t in zip(axes.flat,
                     [noisy, denoised, edges, edges_enhanced],
                     ["带噪原图", "高斯降噪", "查找边缘", "自动对比度增强"]):
    ax.imshow(im, cmap="gray" if im.mode == "L" else None)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.show()
''')

# 12. ImageDraw 几何绘制
add(
    "draw-shapes.py", "ImageDraw 几何绘制",
    "用 ImageDraw 绘制线条、矩形、椭圆、圆弧、弦形、扇形、多边形与圆角矩形，覆盖基础绘图 API。",
    ["绘图", "ImageDraw"],
    '''
"""ImageDraw 几何绘制：基础图形全家福"""
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

img = Image.new("RGB", (420, 320), "white")
d = ImageDraw.Draw(img)

d.line([(20, 40), (120, 40)], fill=(0, 0, 0), width=3)
d.rectangle([150, 20, 260, 90], outline=(30, 144, 255), width=3)
d.ellipse([290, 20, 400, 90], outline=(255, 80, 80), width=3)
d.arc([20, 120, 130, 230], start=30, end=300, fill=(0, 160, 80), width=3)
d.chord([160, 120, 270, 230], start=0, end=120, fill=(255, 215, 0), outline=(0, 0, 0))
d.pieslice([300, 120, 410, 230], start=0, end=270, fill=(200, 100, 255), outline=(0, 0, 0))
d.polygon([(20, 260), (80, 300), (60, 240), (120, 260)], fill=(100, 200, 255))
d.rounded_rectangle([170, 250, 300, 310], radius=20, fill=(255, 150, 100))

plt.figure(figsize=(9, 7))
plt.imshow(img)
plt.axis("off")
plt.title("ImageDraw 几何绘制")
plt.show()
img.save("draw_shapes_demo.png")
''')

# 13. 图像文字与水印
add(
    "draw-text-watermark.py", "文字与水印",
    "尝试加载系统中文字体并绘制文字，在图上叠加半透明水印与斜向平铺水印纹理。",
    ["文字", "水印"],
    '''
"""文字与水印：标题文字 + 半透明水印"""
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

# 生成渐变底图
import numpy as np
xx = np.linspace(180, 120, 360, dtype=np.uint8)
img = Image.fromarray(np.tile(xx, (240, 1)), "L").convert("RGB")
d = ImageDraw.Draw(img)

# 尝试加载系统中文字体（找不到则用默认字体）
font_paths = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc",
              "/System/Library/Fonts/Supplemental/Songti.ttc", "C:/Windows/Fonts/msyh.ttc"]
font = None
for fp in font_paths:
    try:
        font = ImageFont.truetype(fp, 28)
        break
    except Exception:
        continue
if font is None:
    font = ImageFont.load_default()

d.text((24, 90), "示例管理器 DEMO", font=font, fill=(255, 255, 255))

# 半透明水印（平铺）
wm = Image.new("RGBA", img.size, (0, 0, 0, 0))
wd = ImageDraw.Draw(wm)
for x in range(0, 360, 130):
    for y in range(0, 240, 80):
        wd.text((x, y), "WATERMARK", font=font, fill=(255, 255, 255, 60))
img = Image.alpha_composite(img.convert("RGBA"), wm)

plt.figure(figsize=(9, 6))
plt.imshow(img)
plt.axis("off")
plt.title("文字与水印效果")
plt.show()
img.save("watermark_demo.png")
''')

# 14. 验证码生成
add(
    "captcha-generator.py", "验证码生成器",
    "随机 4 字符验证码：随机字体颜色、旋转字符、干扰线与噪点，演示综合绘图应用。",
    ["验证码", "绘图"],
    '''
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
''')

# 15. 图像融合渐变
add(
    "image-blend.py", "图像融合渐变",
    "两张程序化生成的图像用 Image.blend 按不同权重融合，并生成多帧过渡对比。",
    ["合成", "融合"],
    '''
"""图像融合：Image.blend 权重渐变"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 生成两张对比图
W, H = 300, 300
img1 = Image.new("RGB", (W, H), (30, 144, 255))
img2 = Image.new("RGB", (W, H), (255, 165, 0))
d1 = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d2 = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d1.ellipse([60, 60, 240, 240], fill=(255, 255, 255))
d2.polygon([(150, 40), (260, 240), (40, 240)], fill=(255, 255, 255))

alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
fig, axes = plt.subplots(1, 5, figsize=(16, 4))
for ax, a in zip(axes, alphas):
    blended = Image.blend(img1, img2, a)
    ax.imshow(blended)
    ax.set_title(f"alpha={a:.2f}")
    ax.axis("off")
plt.suptitle("Image.blend 图像融合")
plt.tight_layout()
plt.show()
''')

# 16. 蒙版粘贴合成
add(
    "paste-mask.py", "蒙版粘贴合成",
    "用径向渐变蒙版把花朵图与星空底图无缝融合，演示 paste(mask=) 的 alpha 蒙版用法。",
    ["合成", "蒙版"],
    '''
"""蒙版粘贴合成：径向渐变无缝融合"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

W, H = 320, 320

# 底图：深蓝星空 + 随机亮点
bg = Image.new("RGB", (W, H), (8, 16, 48))
rng = np.random.default_rng(3)
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
for _ in range(220):
    d.point((rng.integers(0, W), rng.integers(0, H)), fill=(255, 255, 255))

# 前景：暖色圆（模拟太阳/花朵）
fg = Image.new("RGB", (W, H), (255, 220, 60))
fd = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
fd.ellipse([80, 80, 240, 240], fill=(255, 140, 40))

# 径向渐变蒙版：中心不透明 → 边缘透明
yy, xx = np.mgrid[0:H, 0:W]
dist = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / (W / 2)
mask = np.clip(1 - dist, 0, 1)
mask_img = Image.fromarray((mask * 255).astype(np.uint8), "L")

result = bg.copy()
result.paste(fg, (0, 0), mask_img)

plt.figure(figsize=(8, 8))
plt.imshow(result)
plt.axis("off")
plt.title("蒙版粘贴：径向渐变合成")
plt.show()
result.save("paste_mask_demo.png")
''')

# 17. ASCII 艺术
add(
    "ascii-art.py", "ASCII 艺术转换",
    "把图像亮度映射为字符集输出控制台 ASCII 艺术画，演示像素读取与字符可视化。",
    ["特效", "字符画"],
    '''
"""ASCII 艺术：图像亮度 → 字符画"""
from PIL import Image
import numpy as np

# 程序化生成爱心图案
W, H = 120, 60
img = Image.new("L", (W, H), 0)
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
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
print("\\n".join(out_lines))
''')

# 18. 复古滤镜
add(
    "vintage-filter.py", "复古滤镜与暗角",
    "棕褐色调 + 四周暗角 + 胶片噪点，完整实现老照片风格滤镜，演示多维像素运算。",
    ["特效", "复古"],
    '''
"""复古滤镜：棕褐调 + 暗角 + 噪点"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成"照片"素材
W, H = 360, 260
img = Image.new("RGB", (W, H), (140, 190, 140))
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.rectangle([0, 160, W, H], fill=(90, 140, 90))          # 草地
d.rectangle([140, 120, 220, 180], fill=(200, 150, 120))  # 小房子
d.polygon([(120, 120), (180, 70), (240, 120)], fill=(150, 90, 70))  # 屋顶
d.ellipse([60, 40, 130, 90], fill=(255, 220, 90))        # 太阳

arr = np.asarray(img).astype(np.float32)

# 1) 棕褐色调
gray = arr.mean(axis=2, keepdims=True)
arr = arr * 0.55 + gray * 0.45
arr[..., 0] = np.clip(arr[..., 0] * 1.12, 0, 255)   # R 偏暖
arr[..., 2] = np.clip(arr[..., 2] * 0.88, 0, 255)   # B 偏冷

# 2) 暗角
yy, xx = np.mgrid[0:H, 0:W]
dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
vignette = np.clip(1 - dist * 0.55, 0, 1)[..., None]
arr = arr * vignette

# 3) 胶片噪点
rng = np.random.default_rng(11)
arr = arr + rng.normal(0, 6, arr.shape)

out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(img)
axes[0].set_title("原图")
axes[0].axis("off")
axes[1].imshow(out)
axes[1].set_title("复古滤镜效果")
axes[1].axis("off")
plt.tight_layout()
plt.show()
''')

# 19. 霓虹发光效果
add(
    "glow-effect.py", "霓虹发光效果",
    "提取边缘轮廓 + 多层高斯模糊叠加 + 原图合成，实现霓虹灯管发光效果。",
    ["特效", "发光"],
    '''
"""霓虹发光：边缘 + 高斯模糊叠光"""
from PIL import Image, ImageFilter, ImageChops
import matplotlib.pyplot as plt

# 程序化生成简单图形
W, H = 360, 240
img = Image.new("RGB", (W, H), (10, 10, 25))
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([70, 50, 290, 190], outline=(255, 255, 255), width=3)
d.line([(60, 40), (300, 200)], fill=(255, 255, 255), width=3)

# 提取轮廓（发光源）
edges = img.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda p: 255 if p > 40 else 0)
glow_src = Image.merge("RGB", [edges] * 3)

# 多层高斯模糊叠加发光
glow = Image.new("RGB", (W, H), (0, 0, 0))
for radius, color in [(12, (30, 40, 255)), (7, (120, 140, 255)), (3, (230, 240, 255))]:
    layer = glow_src.filter(ImageFilter.GaussianBlur(radius))
    layer = ImageChops.multiply(layer, Image.new("RGB", (W, H), color))
    glow = ImageChops.add(glow, layer)

# 合成
result = ImageChops.add(img, glow)

plt.figure(figsize=(9, 6))
plt.imshow(result)
plt.axis("off")
plt.title("霓虹发光效果")
plt.show()
result.save("glow_demo.png")
''')

# 20. GIF 动画生成
add(
    "gif-animation.py", "GIF 动画生成",
    "用 Pillow 生成旋转渐变圆的多帧 GIF 动图并保存，演示 save_all/append_images 动画制作。",
    ["GIF", "动画"],
    '''
"""GIF 动画生成：旋转渐变圆"""
from PIL import Image, ImageDraw
import math

W, H = 200, 200
frames = []
for angle in range(0, 360, 15):
    frame = Image.new("RGB", (W, H), (20, 20, 40))
    d = ImageDraw.Draw(frame)
    # 彩色扇区
    for i in range(8):
        a0 = math.radians(angle + i * 45)
        a1 = math.radians(angle + (i + 1) * 45)
        color = [(255, 60, 60), (255, 170, 40), (255, 240, 60), (120, 230, 80),
                 (60, 200, 200), (80, 130, 255), (170, 90, 255), (255, 100, 200)][i]
        d.pieslice([30, 30, 170, 170], a0, a1, fill=color)
    d.ellipse([78, 78, 122, 122], fill=(20, 20, 40))
    frames.append(frame)

frames[0].save("rotation_demo.gif", save_all=True, append_images=frames[1:],
               duration=90, loop=0)
print("已保存 rotation_demo.gif，共", len(frames), "帧")
''')

# 21. 直方图与均衡化
add(
    "histogram-equalize.py", "直方图与均衡化",
    "低对比度图像的直方图分析与直方图均衡化前后对比，用 matplotlib 绘制直方图。",
    ["直方图", "增强"],
    '''
"""直方图与均衡化：低对比度图像增强"""
from PIL import Image, ImageOps
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成低对比度图
W, H = 300, 300
v = np.linspace(60, 130, W, dtype=np.uint8)
img = Image.fromarray(np.tile(v, (H, 1)), "L")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d.ellipse([80, 80, 220, 220], outline=255, width=3)

eq = ImageOps.equalize(img)

fig, axes = plt.subplots(2, 2, figsize=(10, 9))
axes[0, 0].imshow(img, cmap="gray")
axes[0, 0].set_title("原图（低对比度）")
axes[0, 0].axis("off")
axes[0, 1].hist(np.asarray(img).ravel(), bins=64, color="#2e86de")
axes[0, 1].set_title("原图直方图（集中在窄范围）")
axes[1, 0].imshow(eq, cmap="gray")
axes[1, 0].set_title("均衡化后")
axes[1, 0].axis("off")
axes[1, 1].hist(np.asarray(eq).ravel(), bins=64, color="#e17055")
axes[1, 1].set_title("均衡化直方图（分布更均匀）")
plt.tight_layout()
plt.show()
''')

# 22. 九宫格切图
add(
    "nine-grid-split.py", "九宫格切图",
    "把一张程序化生成的图片按 3x3 切分为 9 张小图并展示，演示 crop 批量切片。",
    ["裁剪", "切片"],
    '''
"""九宫格切图：3x3 批量切片"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成 300x300 编号渐变图
W = 300
xx = np.linspace(0, 255, W, dtype=np.uint8)
img = Image.fromarray(np.tile(xx, (W, 1)), "L").convert("RGB")
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
for i in range(9):
    r, c = divmod(i, 3)
    d.rectangle([c * 100, r * 100, c * 100 + 98, r * 100 + 98], outline=(255, 255, 255), width=4)

step = W // 3
tiles = []
for r in range(3):
    for c in range(3):
        tiles.append(img.crop((c * step, r * step, (c + 1) * step, (r + 1) * step)))

fig, axes = plt.subplots(3, 3, figsize=(9, 9))
for ax, tile in zip(axes.flat, tiles):
    ax.imshow(tile)
    ax.axis("off")
plt.suptitle("九宫格切图：3x3 切片")
plt.tight_layout()
plt.show()
''')

# 23. 图像差异检测
add(
    "image-diff.py", "图像差异检测",
    "两张几乎相同的图用 ImageChops.difference 找出差异区域并高亮，演示像素级比对。",
    ["差异检测", "ImageChops"],
    '''
"""图像差异检测：找不同"""
from PIL import Image, ImageChops
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成两张"几乎相同"的图
W, H = 320, 220
base = Image.new("RGB", (W, H), (240, 240, 245))
d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
for i in range(0, W, 40):
    d.line([(i, 0), (i, H)], fill=(200, 200, 210), width=1)
for j in range(0, H, 40):
    d.line([(0, j), (W, j)], fill=(200, 200, 210), width=1)
d.rectangle([40, 40, 120, 100], fill=(255, 200, 100))
d.ellipse([200, 60, 280, 140], fill=(120, 220, 255))

img2 = base.copy()
d2 = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
d2.rectangle([40, 40, 120, 100], fill=(255, 80, 80))     # 颜色不同
d2.ellipse([200, 60, 280, 140], fill=(120, 220, 255))    # 原样
d2.polygon([(150, 150), (170, 190), (130, 190)], fill=(0, 160, 0))  # 新增

diff = ImageChops.difference(base, img2).convert("L")
# 差异区域放大显示
mark = base.copy()
md = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
arr = np.asarray(diff)
ys, xs = np.where(arr > 20)
if len(xs):
    md.rectangle([xs.min() - 6, ys.min() - 6, xs.max() + 6, ys.max() + 6],
                 outline=(255, 0, 0), width=3)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, im, t in zip(axes, [base, img2, mark], ["图 A", "图 B", "差异高亮"]):
    ax.imshow(im)
    ax.set_title(t)
    ax.axis("off")
plt.tight_layout()
plt.show()
''')

# 24. 缩略图墙
add(
    "collage-grid.py", "缩略图墙拼图",
    "把多张程序化生成的渐变图缩略后拼成 2x3 拼图墙，演示批量处理与拼接。",
    ["拼接", "批量"],
    '''
"""缩略图墙：多图拼接 2x3"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 程序化生成 6 张不同色调的渐变图
thumbs = []
for hue_base in range(0, 360, 60):
    W, H = 120, 120
    v = np.linspace(0, 255, W, dtype=np.uint8)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
    # 简化的 HSV 色调色板
    r = int(128 + 127 * np.sin(np.radians(hue_base)))
    g = int(128 + 127 * np.sin(np.radians(hue_base + 120)))
    b = int(128 + 127 * np.sin(np.radians(hue_base + 240)))
    d.ellipse([10, 10, 110, 110], fill=(r, g, b))
    thumb = img.resize((100, 100), Image.Resampling.LANCZOS)
    thumbs.append(thumb)

wall = Image.new("RGB", (100 * 3 + 40, 100 * 2 + 30), "white")
for i, t in enumerate(thumbs):
    r, c = divmod(i, 3)
    wall.paste(t, (10 + c * 110, 10 + r * 110))

plt.figure(figsize=(8, 6))
plt.imshow(wall)
plt.axis("off")
plt.title("缩略图墙 2x3")
plt.show()
wall.save("collage_demo.png")
''')

# 写出 JSON
out_path = os.path.join(os.path.dirname(__file__), "..", "json_examples", "pil_examples.json")
out_path = os.path.normpath(out_path)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"examples": EXAMPLES}, f, ensure_ascii=False, indent=2)
print(f"✅ 已生成 {len(EXAMPLES)} 个 PIL 图像处理示例 → {out_path}")
