// tool-schemas-pil.ts：bulk_pil 12 滤镜家族交互页（144 变体归并）。
// 变体 = 程序化底图 + 家族滤镜 + 一个参数逐档变化；页面 = 同底图 + 同滤镜 + 参数可调，
// 语义与 bulk_pil 变体同源（PIL/ImageFilter/ImageEnhance/ImageOps）。
// 画廊路由专用注册（interactiveGallerySchemas），不进工具箱卡片池。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const PIL_HEAD = `import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

# 程序化演示底图：色带 + 圆环 + 渐变地面（滤镜效果可辨识）
W, H = 480, 320
base = Image.new("RGB", (W, H), "#1f2430")
dr = ImageDraw.Draw(base)
band = ["#e63946", "#f4a261", "#e9c46a", "#8ab17d", "#2a9d8f", "#457b9d", "#5e60ce", "#9d4edd"]
for i, c in enumerate(band):
    x0 = i * W // len(band)
    dr.rectangle([x0, 0, x0 + W // len(band) - 1, H // 2], fill=c)
dr.ellipse([W // 2 - 70, H // 2 - 70, W // 2 + 70, H // 2 + 70], outline="#f1faee", width=5)
for y in range(H // 2 + 10, H, 12):
    t = (y - H // 2) / (H // 2)
    dr.line([(0, y), (W, y)], fill=(int(30 + 90 * t), int(36 + 70 * t), int(48 + 60 * t)), width=6)
`

const PIL_OUT = `result.save("effect.png")
print("已输出 effect.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "effect.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

export interface PilFamily {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const pilFamily = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): PilFamily => ({ value, label, description, fields, body })


const P = (key: string, label: string, def: number, help?: string) => ({
  key, label, type: 'number' as const, default: def, width: 'half' as const, ...(help ? { help } : {})
})

export const PIL_FAMILIES: PilFamily[] = [
  pilFamily('gaussian', 'PIL 高斯模糊',
    'GaussianBlur 半径可调（对应 bulk_pil gaussian 家族的 radius 逐档）。',
    [P('radius', '模糊半径', 4, '像素')],
    (v) => `radius = ${Math.max(0, Number(v.radius) || 0)}
result = base.filter(ImageFilter.GaussianBlur(radius=radius))`),
  pilFamily('grayscale', 'PIL 灰度转换',
    'convert("L") 灰度（grayscale 家族）。',
    [],
    () => `result = base.convert("L")`),
  pilFamily('invert', 'PIL 反色',
    'ImageOps.invert 通道反转（invert 家族）。',
    [],
    () => `result = ImageOps.invert(base)`),
  pilFamily('emboss', 'PIL 浮雕',
    'ImageFilter.EMBOSS 卷积核强度可调（emboss 家族）。',
    [P('gain', '浮雕强度', 1.0)],
    (v) => `gain = max(0.1, ${Number(v.gain) || 1})
k = ImageFilter.EMBOSS
k.gain = gain
result = base.filter(k)`),
  pilFamily('contour', 'PIL 轮廓提取',
    'ImageFilter.CONTOUR 边缘轮廓（contour 家族）。',
    [],
    () => `result = base.filter(ImageFilter.CONTOUR)`),
  pilFamily('solarize', 'PIL 曝光反转',
    'ImageOps.solarize 阈值以上反转（solarize 家族）。',
    [P('threshold', '反转阈值', 128, '0~255')],
    (v) => `threshold = min(255, max(0, ${Math.trunc(Number(v.threshold) || 128)}))
result = ImageOps.solarize(base, threshold=threshold)`),
  pilFamily('posterize', 'PIL 色调分离',
    'ImageOps.posterize 每通道位数可调（posterize 家族）。',
    [P('bits', '每通道位数', 3, '1~8')],
    (v) => `bits = min(8, max(1, ${Math.trunc(Number(v.bits) || 3)}))
result = ImageOps.posterize(base, bits=bits)`),
  pilFamily('mirror', 'PIL 镜像翻转',
    'transpose 左右/上下镜像（mirror 家族）。',
    [{ key: 'axis', label: '方向', type: 'select', default: 'lr', width: 'half', options: [
      { value: 'lr', label: '左右镜像' }, { value: 'tb', label: '上下镜像' }] }],
    (v) => `axis = ${JSON.stringify(String(v.axis ?? 'lr'))}
result = base.transpose(Image.Transpose.FLIP_LEFT_RIGHT if axis == "lr" else Image.Transpose.FLIP_TOP_BOTTOM)`),
  pilFamily('rotate-crop', 'PIL 旋转裁剪',
    'rotate 角度可调 + expand，中心裁剪（rotate-crop 家族）。',
    [P('angle', '旋转角度', 15), P('crop', '裁剪比例%', 80)],
    (v) => `angle = ${Number(v.angle) || 0}
crop_pct = min(100, max(10, ${Math.trunc(Number(v.crop) || 80)}))
rotated = base.rotate(angle, expand=True, fillcolor="#1f2430")
w, h = rotated.size
cw, ch = int(w * crop_pct / 100), int(h * crop_pct / 100)
result = rotated.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2))`),
  pilFamily('enhance-quad', 'PIL 四维增强',
    '亮度/对比度/饱和度/锐度 ImageEnhance 四件套（enhance-quad 家族）。',
    [P('brightness', '亮度', 1.2), P('contrast', '对比度', 1.2), P('color', '饱和度', 1.3), P('sharpness', '锐度', 1.5)],
    (v) => `result = base
for factor_name, factor in [("Brightness", ${Number(v.brightness) || 1}), ("Contrast", ${Number(v.contrast) || 1}), ("Color", ${Number(v.color) || 1}), ("Sharpness", ${Number(v.sharpness) || 1})]:
    result = getattr(ImageEnhance, factor_name)(result).enhance(max(0.0, factor))`),
  pilFamily('gradient-mask', 'PIL 渐变蒙版',
    '线性渐变蒙版与底图合成（gradient-mask 家族）。',
    [{ key: 'dir', label: '方向', type: 'select', default: 'v', width: 'half', options: [
      { value: 'v', label: '垂直渐变' }, { value: 'h', label: '水平渐变' }] }],
    (v) => `direction = ${JSON.stringify(String(v.dir ?? 'v'))}
if direction == "h":
    grad = np.tile(np.linspace(0, 255, W, dtype=np.uint8), (H, 1))
else:
    grad = np.tile(np.linspace(0, 255, H, dtype=np.uint8)[:, None], (1, W))
mask = Image.fromarray(grad, mode="L")
overlay = Image.new("RGB", (W, H), "#0b1020")
result = Image.composite(overlay, base, mask)`),
  pilFamily('pixelate', 'PIL 像素化',
    '缩小再放大马赛克，块大小可调（pixelate 家族）。',
    [P('block', '像素块', 12, '块边长 px')],
    (v) => `block = max(2, ${Math.trunc(Number(v.block) || 12)})
small = base.resize((max(1, W // block), max(1, H // block)), Image.NEAREST)
result = small.resize((W, H), Image.NEAREST)`),
  pilFamily('sepia', 'PIL 复古棕调',
  '灰度 + 色调映射仿旧照片（覆盖 pillow-grayscale-sepia）。',
  [P('strength', '棕调强度', 0.75, '0~1')],
  (v) => `strength = min(1, max(0, ${Number(v.strength) || 0.75}))
gray = base.convert("L")
sepia = Image.merge("RGB", [
    gray.point(lambda p: min(255, int(p * (1 + 0.6 * strength)))),
    gray.point(lambda p: min(255, int(p * (1 + 0.2 * strength)))),
    gray.point(lambda p: int(p * (1 - 0.25 * strength))),
])
result = Image.blend(base, sepia, 0.6 + 0.4 * strength)`),
  pilFamily('pixelart', 'PIL 像素画风',
  '高倍量化 + 最近邻放大（覆盖 pillow-pixel-art）。',
  [P('colors', '色板数', 8), P('scale', '块大小', 10)],
  (v) => `colors = max(2, min(64, ${Math.max(2, Math.trunc(Number(v.colors) || 8))}))
scale = max(2, ${Math.max(2, Math.trunc(Number(v.scale) || 10))})
small = base.resize((W // scale, H // scale))
quant = small.quantize(colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
result = quant.resize((W, H), Image.NEAREST)`),
  pilFamily('glow', 'PIL 辉光效果',
  '亮部提取 + 高斯叠加（覆盖 pillow-glow-effect）。',
  [P('radius', '光晕半径', 9), P('boost', '辉光强度', 1.6)],
  (v) => `radius = max(1, ${Math.max(1, Math.trunc(Number(v.radius) || 9))})
boost = max(0.2, ${Number(v.boost) || 1.6})
bright = base.point(lambda p: max(0, p - 120) * 2)
halo = bright.filter(ImageFilter.GaussianBlur(radius))
glowed = Image.blend(base, Image.blend(base, halo, 0.9), 0.45)
result = glowed.point(lambda p: min(255, int(p * boost)))`),
  pilFamily('vintage', 'PIL 老照片滤镜',
  '棕调 + 暗角 + 噪点三合一（覆盖 pillow-vintage-filter）。',
  [P('noise', '噪点强度', 18)],
  (v) => `import random as _rnd
_rnd.seed(42)
noise = max(0, ${Math.max(0, Math.trunc(Number(v.noise) || 18))})
gray = base.convert("L")
tint = Image.merge("RGB", [gray.point(lambda p: min(255, p + 34)), gray.point(lambda p: min(255, p + 12)), gray.point(lambda p: max(0, p - 22))])
mask = Image.new("L", (W, H), 0)
_md = ImageDraw.Draw(mask)
_md.ellipse([-W * 0.25, -H * 0.25, W * 1.25, H * 1.25], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(60))
vign = Image.composite(tint, Image.new("RGB", (W, H), (30, 22, 14)), mask)
noise_field = np.random.default_rng(42).integers(-noise, noise + 1, (H, W, 1))
arr = np.array(tint).astype(int) + noise_field
result = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"), "RGB")`),
  pilFamily('blend', 'PIL 颜色罩混合',
  '纯色罩按透明度混合（覆盖 pillow-image-blend）。',
  [{ key: 'tint', label: '罩色', type: 'select', default: 'blue', width: 'half', options: [
      { value: 'blue', label: '冷蓝' }, { value: 'warm', label: '暖橙' }, { value: 'green', label: '青绿' }] },
   P('alpha', '混合度', 0.35, '0~1')],
  (v) => `alpha = min(1, max(0, ${Number(v.alpha) || 0.35}))
tints = {"blue": (30, 90, 200), "warm": (240, 140, 40), "green": (40, 180, 140)}
overlay = Image.new("RGB", (W, H), tints[${JSON.stringify(String(v.tint ?? 'blue'))}])
result = Image.blend(base, overlay, alpha)`),
  pilFamily('pastemask', 'PIL 蒙版合成',
  '圆形蒙版贴回中心（覆盖 pillow-paste-mask）。',
  [P('r', '蒙版半径', 90)],
  (v) => `r = max(20, ${Math.max(20, Math.trunc(Number(v.r) || 90))})
patch = base.filter(ImageFilter.GaussianBlur(6)).point(lambda p: min(255, int(p * 1.3)))
mask = Image.new("L", (W, H), 0)
_md = ImageDraw.Draw(mask)
_md.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=255)
result = base.copy()
result.paste(patch, (0, 0), mask)`),
  pilFamily('kernel', 'PIL 自定义卷积',
  '3×3 卷积核选型（锐化/浮雕/轮廓，覆盖 pillow-custom-kernel）。',
  [{ key: 'preset', label: '卷积核', type: 'select', default: 'sharpen', width: 'half', options: [
      { value: 'sharpen', label: '锐化' }, { value: 'emboss', label: '浮雕' }, { value: 'edge', label: '描边' }] }],
  (v) => `preset = ${JSON.stringify(String(v.preset ?? 'sharpen'))}
kernels = {
    "sharpen": (0, -1, 0, -1, 5, -1, 0, -1, 0),
    "emboss": (-2, -1, 0, -1, 1, 1, 0, 1, 2),
    "edge": (-1, -1, -1, -1, 8, -1, -1, -1, -1),
}
k = ImageFilter.Kernel((3, 3), kernels[preset], scale=1 if preset != "edge" else 1, offset=0 if preset != "emboss" else 128)
result = base.filter(k)`),
  pilFamily('pointops', 'PIL 点运算',
  '线性变换 a·x+b 与阈值二值（覆盖 pillow-point-operations）。',
  [P('a', '斜率 a', 1.3), P('b', '截距 b', 10), P('th', '二值阈值', 128)],
  (v) => `a = ${Number(v.a) || 1}
b = ${Math.trunc(Number(v.b) || 0)}
th = ${Math.trunc(Number(v.th) || 128)}
linear = base.point(lambda p: max(0, min(255, int(a * p + b))))
result = Image.blend(linear, linear.convert("L").point(lambda p: 255 if p > th else 0).convert("RGB"), 0.35)`),
  pilFamily('channels', 'PIL 通道分离',
  'R/G/B 单通道强调（覆盖 pillow-color-channels）。',
  [{ key: 'ch', label: '通道', type: 'select', default: 'r', width: 'half', options: [
      { value: 'r', label: '红' }, { value: 'g', label: '绿' }, { value: 'b', label: '蓝' }] }],
  (v) => `ch = ${JSON.stringify(String(v.ch ?? 'r'))}
idx = {"r": 0, "g": 1, "b": 2}[ch]
chs = base.split()
zero = chs[0].point(lambda p: 0)
result = Image.merge("RGB", [chs[0] if idx == 0 else zero, chs[1] if idx == 1 else zero, chs[2] if idx == 2 else zero])`),
  pilFamily('draw', 'PIL 程序绘图',
  '几何图形/多边形/文字绘制（覆盖 pillow-draw-shapes）。',
  [P('shapes', '图形数', 8)],
  (v) => `n = max(3, ${Math.max(3, Math.trunc(Number(v.shapes) || 8))})
canvas = Image.new("RGB", (W, H), "#101418")
d2 = ImageDraw.Draw(canvas)
import random as _r
_r.seed(7)
palette = ["#e63946", "#f4a261", "#2a9d8f", "#457b9d", "#9d4edd"]
for i in range(n):
    c = palette[i % len(palette)]
    x0, y0 = _r.randint(0, W - 60), _r.randint(0, H - 60)
    if i % 3 == 0:
        d2.ellipse([x0, y0, x0 + 60, y0 + 60], outline=c, width=3)
    elif i % 3 == 1:
        d2.rectangle([x0, y0, x0 + 70, y0 + 46], outline=c, width=3)
    else:
        d2.polygon([(x0, y0 + 50), (x0 + 30, y0), (x0 + 60, y0 + 50)], outline=c, width=3)
result = canvas`),
  pilFamily('watermark', 'PIL 文字水印',
  '半透明文字水印（覆盖 pillow-draw-text-watermark）。',
  [{ key: 'text', label: '水印文字', type: 'text', default: 'PyCase', width: 'half' },
   { key: 'pos', label: '位置', type: 'select', default: 'br', width: 'half', options: [
      { value: 'br', label: '右下' }, { value: 'center', label: '居中' }] }],
  (v) => `text = ${JSON.stringify(String(v.text ?? 'PyCase'))}
pos = ${JSON.stringify(String(v.pos ?? 'br'))}
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d3 = ImageDraw.Draw(layer)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
except Exception:
    font = ImageFont.load_default()
bb = d3.textbbox((0, 0), text, font=font)
tw, thh = bb[2] - bb[0], bb[3] - bb[1]
xy = (W - tw - 18, H - thh - 16) if pos == "br" else ((W - tw) // 2, (H - thh) // 2)
d3.text(xy, text, fill=(255, 255, 255, 150), font=font)
result = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")`),
  pilFamily('rotateflip', 'PIL 旋转翻转',
  '角度旋转 + 方向翻转组合（覆盖 pillow-rotate-flip）。',
  [P('angle', '角度', 25),
   { key: 'flip', label: '翻转', type: 'select', default: 'none', width: 'half', options: [
      { value: 'none', label: '不翻转' }, { value: 'lr', label: '左右' }, { value: 'tb', label: '上下' }] }],
  (v) => `angle = ${Number(v.angle) || 0}
flip = ${JSON.stringify(String(v.flip ?? 'none'))}
img = base
if flip == "lr":
    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
elif flip == "tb":
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
result = img.rotate(angle, expand=True, fillcolor="#101418")`),
  pilFamily('croppaste', 'PIL 裁剪拼贴',
  '区域裁剪后错位回贴（覆盖 pillow-crop-paste）。',
  [P('box', '裁剪块', 120), P('dx', '偏移 X', 40), P('dy', '偏移 Y', 24)],
  (v) => `box = max(30, ${Math.max(30, Math.trunc(Number(v.box) || 120))})
dx, dy = ${Math.trunc(Number(v.dx) || 40)}, ${Math.trunc(Number(v.dy) || 24)}
region = base.crop((0, 0, box, box))
result = base.copy()
result.paste(region, (dx, dy))`),
  pilFamily('captcha', 'PIL 验证码生成',
  '随机字符 + 噪点 + 干扰线（覆盖 pillow-captcha-generator）。',
  [P('len', '字符数', 4), P('lines', '干扰线', 4)],
  (v) => `import random as _r, string as _s
_r.seed(42)
ln = max(3, ${Math.max(3, Math.trunc(Number(v.len) || 4))})
lines = max(0, ${Math.max(0, Math.trunc(Number(v.lines) || 4))})
chars = "".join(_r.choices(_s.ascii_uppercase + _s.digits, k=ln))
img2 = Image.new("RGB", (180, 60), (245, 245, 245))
d4 = ImageDraw.Draw(img2)
for _ in range(120):
    d4.point((_r.randint(0, 179), _r.randint(0, 59)), fill=(_r.randint(120, 220),) * 3)
for _ in range(lines):
    d4.line([(_r.randint(0, 180), _r.randint(0, 60)), (_r.randint(0, 180), _r.randint(0, 60))], fill=(_r.randint(80, 200),) * 3, width=1)
try:
    fnt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
except Exception:
    fnt = ImageFont.load_default()
d4.text((14, 12), chars, fill=(40, 40, 40), font=fnt)
result = img2`),
  pilFamily('gifframes', 'PIL GIF 帧生成',
  '多帧动图导出（GIF 逐帧，覆盖 pillow-gif-animation）。',
  [P('frames', '帧数', 8)],
  (v) => `frames = max(2, ${Math.max(2, Math.trunc(Number(v.frames) || 8))})
import math as _m
frames_img = []
for i in range(frames):
    fr = Image.new("P", (160, 120), 20)
    fr.putpalette([v for _i in range(256) for v in (_i, _i, _i)])  # P 模式不设调色板导出全黑
    fd = ImageDraw.Draw(fr)
    cx, cy = 80 + int(52 * _m.cos(2 * _m.pi * i / frames)), 60 + int(38 * _m.sin(2 * _m.pi * i / frames))
    fd.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=230 - i * 8)
    frames_img.append(fr)
frames_img[0].save("effect.png", save_all=False)
result = frames_img[-1].convert("RGB")`),
  pilFamily('ninegrid', 'PIL 九宫格切分',
  '3×3 切片预览（覆盖 pillow-nine-grid-split）。',
  [P('gap', '留白', 4)],
  (v) => `gap = max(0, ${Math.max(0, Math.trunc(Number(v.gap) || 4))})
cw, chh = (W - 2 * gap) // 3, (H - 2 * gap) // 3
canvas = Image.new("RGB", (W, H), "#ffffff")
for r in range(3):
    for c in range(3):
        tile = base.crop((c * W // 3, r * H // 3, (c + 1) * W // 3, (r + 1) * H // 3)).resize((cw, chh))
        canvas.paste(tile, (c * (cw + gap) + gap, r * (chh + gap) + gap))
result = canvas`),
  pilFamily('diff', 'PIL 图像差异',
  '两版本差异高亮（底图 vs 均衡化版本，覆盖 pillow-image-diff）。',
  [P('sens', '敏感度', 40)],
  (v) => `sens = max(5, ${Math.max(5, Math.trunc(Number(v.sens) || 40))})
other = base.filter(ImageFilter.GaussianBlur(3))
diff = np.abs(np.array(base, dtype=int) - np.array(other, dtype=int)).sum(axis=2)
mask = (diff > sens).astype("uint8") * 255
highlight = base.copy()
highlight.paste(Image.new("RGB", (W, H), (255, 40, 40)), (0, 0), Image.fromarray(mask, "L"))
result = highlight`),
  pilFamily('collage', 'PIL 拼贴画',
  '随机小图错落拼贴（覆盖 pillow-collage-grid）。',
  [P('tiles', '拼块数', 12)],
  (v) => `import random as _r
_r.seed(11)
tiles = max(4, ${Math.max(4, Math.trunc(Number(v.tiles) || 12))})
canvas = Image.new("RGB", (W, H), "#0e1116")
for i in range(tiles):
    tw2, th2 = _r.randint(60, 150), _r.randint(50, 120)
    x0, y0 = _r.randint(0, W - tw2), _r.randint(0, H - th2)
    x1, x2 = sorted((_r.randint(0, W - 80), _r.randint(80, W)))
    y1, y2 = sorted((_r.randint(0, H - 60), _r.randint(60, H)))
    patch = base.crop((x1, y1, x2, y2)).resize((tw2, th2))
    canvas.paste(patch, (x0, y0))
result = canvas`),
  pilFamily('gradient', 'PIL 渐变生成',
  '双色线性渐变（覆盖 pillow-gradient-generator）。',
  [{ key: 'dir', label: '方向', type: 'select', default: 'v', width: 'half', options: [
      { value: 'v', label: '垂直' }, { value: 'h', label: '水平' }, { value: 'd', label: '对角' }] }],
  (v) => `direction = ${JSON.stringify(String(v.dir ?? 'v'))}
c0 = np.array([30, 60, 160], dtype=float)
c1 = np.array([250, 190, 60], dtype=float)
if direction == "v":
    t = np.tile(np.linspace(0, 1, H)[:, None, None], (1, W, 1))
elif direction == "h":
    t = np.tile(np.linspace(0, 1, W)[None, :, None], (H, 1, 1))
else:
    yy, xx = np.mgrid[0:H, 0:W]
    t = ((xx / W + yy / H) / 2)[:, :, None]
arr = (c0 * (1 - t) + c1 * t).astype("uint8")
result = Image.fromarray(arr, "RGB")`),
  pilFamily('gallery', 'PIL 滤镜画廊',
  '六种滤镜同框对比（覆盖 pillow-filter-gallery）。',
  [],
  () => `filters = [
    ("原图", base),
    ("模糊", base.filter(ImageFilter.GaussianBlur(4))),
    ("浮雕", base.filter(ImageFilter.EMBOSS)),
    ("轮廓", base.filter(ImageFilter.CONTOUR)),
    ("细节", base.filter(ImageFilter.DETAIL)),
    ("边缘增强", base.filter(ImageFilter.EDGE_ENHANCE)),
]
cw2, ch2 = W // 3, H // 2
canvas = Image.new("RGB", (W, H), "#0e1116")
for i, (name, im) in enumerate(filters):
    canvas.paste(im.resize((cw2 - 4, ch2 - 4)), ((i % 3) * cw2 + 2, (i // 3) * ch2 + 2))
result = canvas`),
]

// ---------------------------------------------------------------------------
// PIL 滤镜实验室：12 滤镜家族归并单页
// ---------------------------------------------------------------------------
const PIL_FILTER_FIELD: FieldSpec = {
  key: 'type',
  label: '滤镜',
  type: 'select',
  default: 'gaussian',
  width: 'full',
  options: PIL_FAMILIES.map((f) => ({ value: f.value, label: f.label }))
}

export const pilLabSchema: InteractiveToolSchema = {
  id: 'interactive:pil-lab',
  title: 'PIL 滤镜实验室',
  description: 'bulk_pil 12 滤镜家族的归并页：程序化演示底图，选滤镜、调参数，Pillow 出图。',
  tags: ['图像', 'PIL'],
  fields: (v) => {
    const f = PIL_FAMILIES.find((x) => x.value === v.type) ?? PIL_FAMILIES[0]!
    return [PIL_FILTER_FIELD, ...f.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '滤镜', value: String(v.type ?? 'gaussian') }] }),
  headerFor: (v) => {
    const f = PIL_FAMILIES.find((x) => x.value === v.type) ?? PIL_FAMILIES[0]!
    return { title: f.label, description: f.description }
  },
  pyCode: (v) => {
    const f = PIL_FAMILIES.find((x) => x.value === v.type) ?? PIL_FAMILIES[0]!
    return `${PIL_HEAD}\n${f.body(v)}\n${PIL_OUT}`
  }
}
