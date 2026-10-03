// tool-schemas-pil.ts：bulk_pil 12 滤镜家族交互页（144 变体归并）。
// 变体 = 程序化底图 + 家族滤镜 + 一个参数逐档变化；页面 = 同底图 + 同滤镜 + 参数可调，
// 语义与 bulk_pil 变体同源（PIL/ImageFilter/ImageEnhance/ImageOps）。
// 画廊路由专用注册（interactiveGallerySchemas），不进工具箱卡片池。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const PIL_HEAD = `import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

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
result = small.resize((W, H), Image.NEAREST)`)
]

// ---------------------------------------------------------------------------
// PIL 滤镜实验室：12 滤镜家族归并单页
// ---------------------------------------------------------------------------
const PIL_FILTER_FIELD: FieldSpec = {
  key: 'filter',
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
    const f = PIL_FAMILIES.find((x) => x.value === v.filter) ?? PIL_FAMILIES[0]!
    return [PIL_FILTER_FIELD, ...f.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '滤镜', value: String(v.filter ?? 'gaussian') }] }),
  pyCode: (v) => {
    const f = PIL_FAMILIES.find((x) => x.value === v.filter) ?? PIL_FAMILIES[0]!
    return `${PIL_HEAD}\n${f.body(v)}\n${PIL_OUT}`
  }
}
