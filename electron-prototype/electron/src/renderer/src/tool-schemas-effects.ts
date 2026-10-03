// tool-schemas-effects.ts：V3 图像效果实验室 ×25——PIL/OpenCV 单文件输入 → 效果处理 → PNG 产物预览。
// 形态：file 字段选图片 → 参数调优 → sidecar 运行（PIL/OpenCV）→ PNG 进抽屉预览。
// 只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const INVALID = '# 选择图片文件后自动生成代码'

const FILE_FIELD = {
  key: 'file',
  label: '图片文件',
  type: 'file' as const,
  required: true,
  accept: ['png', 'jpg', 'jpeg', 'webp', 'bmp']
}

// PIL 载入 + 保存公共段（兼容 RGBA→RGB 转 jpg）
// ---------------------------------------------------------------------------
// PIL 组：灰度 / 反色 / 高斯模糊 / 锐化 / 像素化 / 旋转 / Gamma / 亮度对比度 / 通道分离 / 老照片
// ---------------------------------------------------------------------------
function pilEffect(
  id: string,
  title: string,
  description: string,
  params: InteractiveToolSchema['fields'],
  body: (v: Record<string, unknown>) => string
): InteractiveToolSchema {
  return {
    id: `interactive:${id}`,
    title,
    description,
    tags: ['图片', '效果'],
    fields: [FILE_FIELD, ...params],
    computeVia: 'sidecar',
    compute: (v) => {
      if (!str(v.file)) return { error: '请选择图片文件' }
      const rows = params.filter((f) => v[f.key] !== undefined).map((f) => ({ label: f.label, value: str(v[f.key]) }))
      return { rows: [{ label: '源文件', value: str(v.file), copy: true }, ...rows] }
    },
    pyCode: (v) => {
      const file = str(v.file)
      if (!file) return INVALID
      void params
      return `"""${title}（PIL）。"""
import json

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

im = Image.open(${JSON.stringify(file)}).convert("RGB")
${body(v)}
im.save("effect.png")
print("已输出 effect.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "effect.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`
    }
  }
}

export const grayscaleSchema = pilEffect(
  'img-grayscale',
  '灰度化',
  '转为灰度图（L 模式）。',
  [],
  () => 'result = im.convert("L")'
)

export const invertSchema = pilEffect(
  'img-invert',
  '反色',
  '颜色反转（ImageOps.invert）。',
  [],
  () => 'result = ImageOps.invert(im)'
)

export const gaussBlurSchema = pilEffect(
  'img-gauss-blur',
  '高斯模糊',
  '高斯模糊（半径可调）。',
  [{ key: 'radius', label: '模糊半径', type: 'number', default: 5, width: 'half' }],
  (v) => {
    const r = Math.max(1, Number(v.radius ?? 5) || 5)
    return `result = im.filter(ImageFilter.GaussianBlur(radius=${r}))`
  }
)

export const sharpenSchema = pilEffect(
  'img-sharpen',
  '锐化',
  '图像锐化（锐度倍数可调）。',
  [{ key: 'factor', label: '锐度倍数', type: 'number', default: 2, width: 'half' }],
  (v) => {
    const f = Math.max(1, Number(v.factor ?? 2) || 2)
    return `result = ImageEnhance.Sharpness(im).enhance(${f})`
  }
)

export const pixelateSchema = pilEffect(
  'img-pixelate',
  '像素化',
  '马赛克像素化（缩到极小再放大）。',
  [{ key: 'blockSize', label: '色块大小', type: 'number', default: 16, width: 'half' }],
  (v) => {
    const b = Math.max(2, Number(v.blockSize ?? 16) || 16)
    return `w, h = im.size
small = im.resize((max(1, w // ${b}), max(1, h // ${b})), Image.NEAREST)
result = small.resize((w, h), Image.NEAREST)`
  }
)

export const rotateSchema = pilEffect(
  'img-rotate',
  '旋转与翻转',
  '按角度旋转（expand 保持内容）。',
  [{ key: 'angle', label: '旋转角度', type: 'number', default: 45, width: 'half' }],
  (v) => {
    const a = Number(v.angle ?? 45) || 0
    return `result = im.rotate(${a}, expand=True, fillcolor=(255, 255, 255))`
  }
)

export const gammaSchema = pilEffect(
  'img-gamma',
  'Gamma 校正',
  'Gamma 亮度校正（<1 变亮 / >1 变暗）。',
  [{ key: 'gamma', label: 'Gamma 值', type: 'number', default: 1.5, width: 'half' }],
  (v) => {
    const g = Math.max(0.1, Number(v.gamma ?? 1.5) || 1.5)
    return `lut = [min(255, int((i / 255) ** (1 / ${g}) * 255)) for i in range(256)]
result = im.point(lut * len(im.getbands()))`
  }
)

export const brightnessContrastSchema = pilEffect(
  'img-brightness-contrast',
  '亮度/对比度',
  '亮度与对比度倍数调节（1.0 = 原样）。',
  [
    { key: 'brightness', label: '亮度倍数', type: 'number', default: 1.2, width: 'half' },
    { key: 'contrast', label: '对比度倍数', type: 'number', default: 1.1, width: 'half' }
  ],
  (v) => {
    const b = Math.max(0.1, Number(v.brightness ?? 1.2) || 1)
    const c = Math.max(0.1, Number(v.contrast ?? 1.1) || 1)
    return `result = ImageEnhance.Brightness(im).enhance(${b})
result = ImageEnhance.Contrast(result).enhance(${c})`
  }
)

export const channelSplitSchema = pilEffect(
  'img-channel-split',
  '通道分离',
  'RGB 通道分离 → 三张单通道灰度图并列拼合。',
  [],
  () => `import numpy as np

arr = np.array(im)
r = arr[:, :, 0]; g = arr[:, :, 1]; b = arr[:, :, 2]
result = np.concatenate([r, g, b], axis=1)  # 水平拼接三通道灰度图
result = Image.fromarray(result, mode="L")`
)

export const oldPhotoSchema = pilEffect(
  'img-old-photo',
  '老照片效果',
  '去色 + 棕褐色调（向量化，无逐像素循环）。',
  [],
  () => `import numpy as np

gray = np.array(im.convert("L"), dtype=np.float64)
r = np.clip(gray * 1.1, 0, 255).astype(np.uint8)
g = gray.astype(np.uint8)
b = np.clip(gray * 0.75, 0, 255).astype(np.uint8)
result = Image.fromarray(np.stack([r, g, b], axis=2))`
)

// ---------------------------------------------------------------------------
// OpenCV 组：Canny / Sobel / 阈值 / 轮廓 / 高斯 / 形态学 / 霍夫 / 均衡化 / 伪彩色 / 距离变换
// ---------------------------------------------------------------------------
function cvEffect(
  id: string,
  title: string,
  description: string,
  params: InteractiveToolSchema['fields'],
  body: (v: Record<string, unknown>) => string
): InteractiveToolSchema {
  return {
    id: `interactive:${id}`,
    title,
    description,
    tags: ['图片', 'OpenCV'],
    fields: [FILE_FIELD, ...params],
    computeVia: 'sidecar',
    compute: (v) => {
      if (!str(v.file)) return { error: '请选择图片文件' }
      const rows = params.filter((f) => v[f.key] !== undefined).map((f) => ({ label: f.label, value: str(v[f.key]) }))
      return { rows: [{ label: '源文件', value: str(v.file), copy: true }, ...rows] }
    },
    pyCode: (v) => {
      const file = str(v.file)
      if (!file) return INVALID
      return `"""${title}（OpenCV）。"""
import json

import cv2
import numpy as np

im = cv2.imread(${JSON.stringify(file)})
if im is None:
    raise SystemExit("无法读取图片")
${body(v)}
cv2.imwrite("effect.png", result)
print("已输出 effect.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "effect.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`
    }
  }
}

export const cannyEdgeSchema = cvEffect(
  'img-canny',
  'Canny 边缘检测',
  'Canny 边缘检测（双阈值可调）。',
  [
    { key: 'low', label: '低阈值', type: 'number', default: 100, width: 'half' },
    { key: 'high', label: '高阈值', type: 'number', default: 200, width: 'half' }
  ],
  (v) => {
    const lo = Math.max(1, Number(v.low ?? 100) || 100)
    const hi = Math.max(lo + 1, Number(v.high ?? 200) || 200)
    return `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
result = cv2.Canny(gray, ${lo}, ${hi})`
  }
)

export const sobelSchema = cvEffect(
  'img-sobel',
  'Sobel 梯度',
  'Sobel 梯度算子（X+Y 方向取绝对值合成）。',
  [],
  () => `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
result = np.abs(sx) + np.abs(sy)
result = np.clip(result, 0, 255).astype(np.uint8)`
)

export const thresholdSchema = cvEffect(
  'img-threshold',
  '阈值分割',
  '全局阈值 + 自适应阈值并列对比。',
  [{ key: 'thresh', label: '阈值', type: 'number', default: 127, width: 'half' }],
  (v) => {
    const t = Math.max(1, Number(v.thresh ?? 127) || 127)
    return `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
_, global_t = cv2.threshold(gray, ${t}, 255, cv2.THRESH_BINARY)
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
result = np.hstack([global_t, adaptive])`
  }
)

export const morphologySchema = cvEffect(
  'img-morphology',
  '形态学运算',
  '开运算/闭运算/梯度（核大小可调）。',
  [
    {
      key: 'op',
      label: '运算',
      type: 'select',
      default: 'open',
      width: 'half',
      options: [
        { value: 'open', label: '开运算' },
        { value: 'close', label: '闭运算' },
        { value: 'gradient', label: '梯度' }
      ]
    },
    { key: 'kernel', label: '核大小', type: 'number', default: 5, width: 'half' }
  ],
  (v) => {
    const op = ['open', 'close', 'gradient'].includes(str(v.op)) ? str(v.op) : 'open'
    const k = Math.max(3, Math.trunc(Number(v.kernel ?? 5)) | 1)
    return `kernel = np.ones((${k}, ${k}), np.uint8)
OPS = {
    "open": cv2.MORPH_OPEN,
    "close": cv2.MORPH_CLOSE,
    "gradient": cv2.MORPH_GRADIENT,
}
result = cv2.morphologyEx(im, OPS["${op}"], kernel)`
  }
)

export const histEqSchema = cvEffect(
  'img-hist-eq',
  '直方图均衡',
  '灰度 + 彩色两路直方图均衡化并列对比。',
  [],
  () => `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
eq_gray = cv2.equalizeHist(gray)
yuv = cv2.cvtColor(im, cv2.COLOR_BGR2YUV)
yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
eq_color = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
result = np.hstack([eq_gray, eq_color])`
)

export const falseColorSchema = cvEffect(
  'img-false-color',
  '伪彩色映射',
  '灰度图伪彩色映射（COLORMAP_JET）。',
  [],
  () => `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
result = cv2.applyColorMap(gray, cv2.COLORMAP_JET)`
)

export const contourSchema = cvEffect(
  'img-contour',
  '轮廓检测',
  '轮廓提取并在原图上绘制（面积前 20 个轮廓）。',
  [],
  () => `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 100, 200)
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]
result = im.copy()
cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
print(f"检测到 {len(contours)} 个轮廓")`
)

export const houghLinesSchema = cvEffect(
  'img-hough-lines',
  '霍夫直线',
  '霍夫变换检测直线并在原图绘制。',
  [],
  () => `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 100, 200)
result = im.copy()
lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=10)
if lines is not None:
    for line in lines[:50]:
        x1, y1, x2, y2 = line[0]
        cv2.line(result, (x1, y1), (x2, y2), (0, 0, 255), 2)
    print(f"检测到 {len(lines)} 条直线")
else:
    print("未检测到直线")`
)

export const distanceTransformSchema = cvEffect(
  'img-distance-transform',
  '距离变换',
  '二值化后的距离变换可视化。',
  [{ key: 'thresh', label: '二值化阈值', type: 'number', default: 127, width: 'half' }],
  (v) => {
    const t = Math.max(1, Number(v.thresh ?? 127) || 127)
    return `gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, ${t}, 255, cv2.THRESH_BINARY)
dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
result = np.clip(dist / dist.max() * 255, 0, 255).astype(np.uint8) if dist.max() > 0 else dist.astype(np.uint8)`
  }
)

// ---------------------------------------------------------------------------
// 效果×2 续（ascii 字符画 / 验证码——纯前端或 PIL 均可，页化为 sidecar）
// ---------------------------------------------------------------------------
export const asciiArtSchema: InteractiveToolSchema = {
  id: 'interactive:ascii-art',
  title: 'ASCII 字符画',
  description: '图片 → 字符画（灰度映射到字符梯度，列宽可调），结果以文本块展示。',
  tags: ['图片', '特效'],
  fields: [
    FILE_FIELD,
    { key: 'cols', label: '列宽（字符数）', type: 'number', default: 80, width: 'half', help: '20~200' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '源文件', value: str(v.file), copy: true }] } : { error: '请选择图片文件' },
  pyCode: (v) => {
    const file = str(v.file)
    const cols = Math.max(20, Math.min(200, Math.trunc(Number(v.cols ?? 80)) || 80))
    if (!file) return INVALID
    return `"""ASCII 字符画（灰度映射字符梯度）。"""
from PIL import Image

CHARS = " .:-=+*#%@"
im = Image.open(${JSON.stringify(file)}).convert("L")
ratio = im.size[1] / im.size[0] * 0.55  # 终端字符高宽比修正
im = im.resize((${cols}, int(${cols} * ratio)))
pixels = list(im.getdata())
lines = []
for y in range(im.size[1]):
    row = "".join(CHARS[min(9, pixels[y * im.size[0] + x] * 10 // 256)] for x in range(im.size[0]))
    lines.append(row)
print("<<<JSON>>>")
print(json.dumps({"text": "\\n".join(lines)}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const EFFECT_SCHEMAS: InteractiveToolSchema[] = [
  grayscaleSchema,
  invertSchema,
  gaussBlurSchema,
  sharpenSchema,
  pixelateSchema,
  rotateSchema,
  gammaSchema,
  brightnessContrastSchema,
  channelSplitSchema,
  oldPhotoSchema,
  cannyEdgeSchema,
  sobelSchema,
  thresholdSchema,
  morphologySchema,
  histEqSchema,
  falseColorSchema,
  contourSchema,
  houghLinesSchema,
  distanceTransformSchema,
  asciiArtSchema
]
