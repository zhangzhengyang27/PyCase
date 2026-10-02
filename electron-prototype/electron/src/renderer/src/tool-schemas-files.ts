// tool-schemas-files.ts：B 档文件管道批量工具——图片 10 + Office 4（W6 收尾批）。
// 批量工具形态：dir 字段选目录 → pyCode 产物在 adhoc 工作区 CWD 展开 → run_images
// 推回抽屉预览（sidecar 上限 12 张）。单文件工具复用 file 字段。
// 依赖：Pillow（图片）、openpyxl / pypdf（Office，共享 venv 已装）。
// 只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const INVALID_CODE = '# 选择目录或文件后自动生成代码'
const str = (v: unknown): string => String(v ?? '')

const IMG_EXTS = ['png', 'jpg', 'jpeg', 'webp', 'bmp']
// 各批量工具共享的 Python 序章：切目录、收集图片、报告数量
const COLLECT = (srcDir: string) => `import glob, os

SRC = ${JSON.stringify(srcDir)}
files = sorted(
    f for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
    for f in glob.glob(os.path.join(SRC, ext))
)
if not files:
    raise SystemExit("目录里没有图片")
print(f"共 {len(files)} 张图片待处理")
`

function jpgGuard(varName: string): string {
  return `if ${varName}.mode in ("RGBA", "P"):\n    ${varName} = ${varName}.convert("RGB")`
}

// ---------------------------------------------------------------------------
// 1. 批量缩放
// ---------------------------------------------------------------------------
export const batchResizeSchema: InteractiveToolSchema = {
  id: 'interactive:batch-resize',
  title: '批量缩放',
  description: '目录内全部图片按长边上限等比缩放（thumbnail 只缩不放），产物逐张出现在抽屉预览（上限 12 张）。',
  tags: ['图片', '批量'],
  fields: [
    { key: 'dir', label: '图片目录', type: 'dir', required: true },
    { key: 'maxSide', label: '长边上限(px)', type: 'number', default: 1024, width: 'half' },
    {
      key: 'format',
      label: '输出格式',
      type: 'select',
      default: 'png',
      width: 'half',
      options: [
        { value: 'png', label: 'PNG' },
        { value: 'jpg', label: 'JPG' }
      ]
    }
  ],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    const maxSide = Math.trunc(Number(v.maxSide))
    if (!Number.isFinite(maxSide) || maxSide < 16 || maxSide > 20000) return { error: '长边上限需为 16~20000 的整数' }
    return {
      rows: [
        { label: '源目录', value: dir, copy: true },
        { label: '长边上限', value: `${maxSide} px` },
        { label: '输出格式', value: str(v.format ?? 'png').toUpperCase() }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const maxSide = Math.trunc(Number(v.maxSide))
    const fmt = str(v.format ?? 'png')
    if (!dir || !Number.isFinite(maxSide) || maxSide < 16) return INVALID_CODE
    return `"""批量缩放：长边上限 ${maxSide}px。"""
from PIL import Image

${COLLECT(dir)}
for i, f in enumerate(files, 1):
    im = Image.open(f)
    im.thumbnail((${maxSide}, ${maxSide}))
    ${jpgGuard('im')}
    out = f"resized_{i:03d}.${fmt}"
    if "${fmt}" == "jpg":
        im.save(out, quality=90)
    else:
        im.save(out)
    print(f"{os.path.basename(f)} → {out} {im.size[0]}x{im.size[1]}")
`
  }
}

// ---------------------------------------------------------------------------
// 2. 批量格式转换
// ---------------------------------------------------------------------------
export const batchConvertSchema: InteractiveToolSchema = {
  id: 'interactive:batch-convert',
  title: '批量格式转换',
  description: '目录内全部图片转为目标格式（JPG 自动白底），产物抽屉预览。',
  tags: ['图片', '批量'],
  fields: [
    { key: 'dir', label: '图片目录', type: 'dir', required: true },
    {
      key: 'format',
      label: '目标格式',
      type: 'select',
      default: 'webp',
      width: 'half',
      options: [
        { value: 'png', label: 'PNG' },
        { value: 'jpg', label: 'JPG' },
        { value: 'webp', label: 'WebP' }
      ]
    }
  ],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    return {
      rows: [
        { label: '源目录', value: dir, copy: true },
        { label: '目标格式', value: str(v.format ?? 'webp').toUpperCase() }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const fmt = str(v.format ?? 'webp')
    if (!dir) return INVALID_CODE
    return `"""批量格式转换 → ${fmt.toUpperCase()}。"""
from PIL import Image

${COLLECT(dir)}
for i, f in enumerate(files, 1):
    im = Image.open(f)
    ${jpgGuard('im')}
    out = f"converted_{i:03d}.${fmt}"
    if "${fmt}" == "jpg":
        im.save(out, quality=90)
    else:
        im.save(out)
    print(f"{os.path.basename(f)} → {out}")
`
  }
}

// ---------------------------------------------------------------------------
// 3. 批量裁剪比例（居中裁）
// ---------------------------------------------------------------------------
export const batchCropSchema: InteractiveToolSchema = {
  id: 'interactive:batch-crop',
  title: '批量裁剪比例',
  description: '目录内全部图片居中裁剪到目标宽高比（16:9 / 1:1 / 4:3），产物抽屉预览。',
  tags: ['图片', '批量'],
  fields: [
    { key: 'dir', label: '图片目录', type: 'dir', required: true },
    {
      key: 'ratio',
      label: '目标比例',
      type: 'select',
      default: '1:1',
      width: 'half',
      options: [
        { value: '1:1', label: '1:1（方形）' },
        { value: '16:9', label: '16:9（宽屏）' },
        { value: '4:3', label: '4:3' }
      ]
    }
  ],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    return {
      rows: [
        { label: '源目录', value: dir, copy: true },
        { label: '目标比例', value: str(v.ratio ?? '1:1') }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const ratio = str(v.ratio ?? '1:1')
    const [rw, rh] = ratio.split(':').map(Number)
    if (!dir || !Number.isFinite(rw) || !Number.isFinite(rh)) return INVALID_CODE
    return `"""批量居中裁剪到 ${ratio}。"""
from PIL import Image

${COLLECT(dir)}
RW, RH = ${rw}, ${rh}
for i, f in enumerate(files, 1):
    im = Image.open(f).convert("RGB")
    w, h = im.size
    if w / h > RW / RH:
        cw = round(h * RW / RH)
        box = ((w - cw) // 2, 0, (w - cw) // 2 + cw, h)
    else:
        ch = round(w * RH / RW)
        box = (0, (h - ch) // 2, w, (h - ch) // 2 + ch)
    out = f"cropped_{i:03d}.png"
    im.crop(box).save(out)
    print(f"{os.path.basename(f)} → {out}")
`
  }
}

// ---------------------------------------------------------------------------
// 4. 批量水印（Pillow 内置可缩放默认字体，跨平台无字体文件依赖）
// ---------------------------------------------------------------------------
export const batchWatermarkSchema: InteractiveToolSchema = {
  id: 'interactive:batch-watermark',
  title: '批量水印',
  description: '目录内全部图片加文字水印（右下角或平铺），用 Pillow 内置可缩放字体（无需字体文件）。',
  tags: ['图片', '批量'],
  fields: [
    { key: 'dir', label: '图片目录', type: 'dir', required: true },
    { key: 'text', label: '水印文字', type: 'text', required: true, placeholder: '@ 我的作品' },
    {
      key: 'position',
      label: '位置',
      type: 'select',
      default: 'corner',
      width: 'half',
      options: [
        { value: 'corner', label: '右下角' },
        { value: 'tile', label: '平铺' }
      ]
    },
    { key: 'fontSize', label: '字号', type: 'number', default: 48, width: 'half' }
  ],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    if (!str(v.text)) return { error: '请输入水印文字' }
    return {
      rows: [
        { label: '源目录', value: dir, copy: true },
        { label: '水印', value: `${str(v.text)}（${str(v.position ?? 'corner') === 'tile' ? '平铺' : '右下角'}）` }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const text = str(v.text)
    const fontSize = Math.trunc(Number(v.fontSize ?? 48))
    const tile = str(v.position ?? 'corner') === 'tile'
    if (!dir || !text) return INVALID_CODE
    return `"""批量水印：${tile ? '平铺' : '右下角'}。"""
from PIL import Image, ImageDraw, ImageFont

${COLLECT(dir)}
font = ImageFont.load_default(size=${Number.isFinite(fontSize) && fontSize >= 8 ? fontSize : 48})
WM = ${JSON.stringify(text)}
for i, f in enumerate(files, 1):
    im = Image.open(f).convert("RGBA")
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), WM, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if ${tile ? 'True' : 'False'}:
        step_x, step_y = tw + 60, th + 60
        yy = 12
        while yy < im.size[1]:
            xx = 12
            while xx < im.size[0]:
                d.text((xx, yy), WM, font=font, fill=(255, 255, 255, 110))
                xx += step_x
            yy += step_y
    else:
        d.text((im.size[0] - tw - 24, im.size[1] - th - 24), WM, font=font, fill=(255, 255, 255, 160))
    out = f"wm_{i:03d}.png"
    Image.alpha_composite(im, layer).convert("RGB").save(out, quality=92)
    print(f"{os.path.basename(f)} → {out}")
`
  }
}

// ---------------------------------------------------------------------------
// 5. 主色调提取（单文件；量化取主色 + 输出 swatch 色板图）
// ---------------------------------------------------------------------------
export const paletteSchema: InteractiveToolSchema = {
  id: 'interactive:palette',
  title: '主色调提取',
  description: '量化提取图片主色（前 6 色 + 占比），并生成色板图在抽屉预览。',
  tags: ['图片', '分析'],
  fields: [
    { key: 'file', label: '图片文件', type: 'file', required: true, accept: IMG_EXTS },
    { key: 'colors', label: '主色数量', type: 'number', default: 6, width: 'half' }
  ],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择图片文件' }
    const n = Math.trunc(Number(v.colors ?? 6))
    if (!Number.isFinite(n) || n < 2 || n > 12) return { error: '主色数量需为 2~12 的整数' }
    return {
      rows: [
        { label: '源文件', value: file, copy: true },
        { label: '主色数量', value: String(n) }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const n = Math.trunc(Number(v.colors ?? 6))
    if (!file || !Number.isFinite(n) || n < 2) return INVALID_CODE
    return `"""主色调提取：量化 ${Number.isFinite(n) && n <= 12 ? n : 6} 色 + 色板图。"""
from PIL import Image, ImageDraw

im = Image.open(${JSON.stringify(file)}).convert("RGB")
q = im.quantize(colors=${Number.isFinite(n) && n <= 12 ? n : 6})
pal = q.getpalette()
counts = sorted(q.getcolors(), reverse=True)
total = sum(c for c, _ in counts)
swatches = []
for cnt, idx in counts:
    r, g, b = pal[idx * 3], pal[idx * 3 + 1], pal[idx * 3 + 2]
    pct = cnt / total * 100
    print(f"#{r:02x}{g:02x}{b:02x}  {pct:5.1f}%")
    swatches.append((r, g, b, pct))
sw = Image.new("RGB", (120 * len(swatches), 80), (255, 255, 255))
d = ImageDraw.Draw(sw)
for i, (r, g, b, pct) in enumerate(swatches):
    d.rectangle([i * 120, 0, (i + 1) * 120 - 4, 79], fill=(r, g, b))
sw.save("palette.png")
print("色板图: palette.png")
`
  }
}

// ---------------------------------------------------------------------------
// 6. GIF 帧提取
// ---------------------------------------------------------------------------
export const gifExtractSchema: InteractiveToolSchema = {
  id: 'interactive:gif-extract',
  title: 'GIF 帧提取',
  description: '把 GIF 逐帧导出为 PNG 序列（抽屉预览前 12 帧），并报告帧数与尺寸。',
  tags: ['图片', 'GIF'],
  fields: [{ key: 'file', label: 'GIF 文件', type: 'file', required: true, accept: ['gif'] }],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择 GIF 文件' }
    return { rows: [{ label: '源文件', value: file, copy: true }] }
  },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return INVALID_CODE
    return `"""GIF 帧提取 → PNG 序列。"""
from PIL import Image

im = Image.open(${JSON.stringify(file)})
n = 0
for frame in range(getattr(im, "n_frames", 1)):
    im.seek(frame)
    n += 1
    im.convert("RGBA").save(f"frame_{frame:03d}.png")
print(f"共 {n} 帧，尺寸 {im.size[0]}x{im.size[1]}")
`
  }
}

// ---------------------------------------------------------------------------
// 7. 图片合成 GIF
// ---------------------------------------------------------------------------
export const gifComposeSchema: InteractiveToolSchema = {
  id: 'interactive:gif-compose',
  title: '图片合成 GIF',
  description: '目录内图片按文件名排序合成动图（尺寸对齐首图，可调帧延时与循环次数）。',
  tags: ['图片', 'GIF'],
  fields: [
    { key: 'dir', label: '图片目录', type: 'dir', required: true },
    { key: 'duration', label: '每帧延时(ms)', type: 'number', default: 200, width: 'half' },
    { key: 'loop', label: '循环次数(0=无限)', type: 'number', default: 0, width: 'half' }
  ],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    const duration = Math.trunc(Number(v.duration ?? 200))
    if (!Number.isFinite(duration) || duration < 20) return { error: '每帧延时应 ≥20ms' }
    return {
      rows: [
        { label: '源目录', value: dir, copy: true },
        { label: '帧延时', value: `${duration} ms` },
        { label: '循环', value: str(v.loop ?? '0') === '0' ? '无限' : `${str(v.loop)} 次` }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const duration = Math.trunc(Number(v.duration ?? 200))
    const loop = Math.trunc(Number(v.loop ?? 0))
    if (!dir || !Number.isFinite(duration) || duration < 20) return INVALID_CODE
    return `"""图片合成 GIF（尺寸对齐首图）。"""
from PIL import Image

${COLLECT(dir)}
frames = []
for f in files:
    im = Image.open(f).convert("RGB")
    if frames and im.size != frames[0].size:
        im = im.resize(frames[0].size)
    frames.append(im)
frames[0].save("out.gif", save_all=True, append_images=frames[1:],
               duration=${Number.isFinite(duration) && duration >= 20 ? duration : 200}, loop=${Number.isFinite(loop) && loop >= 0 ? loop : 0})
print(f"已合成 out.gif：{len(frames)} 帧")
`
  }
}

// ---------------------------------------------------------------------------
// 8. 批量亮度/对比度
// ---------------------------------------------------------------------------
export const batchEnhanceSchema: InteractiveToolSchema = {
  id: 'interactive:batch-enhance',
  title: '批量亮度/对比度',
  description: '目录内全部图片按百分比调亮度与对比度（100 = 原样），产物抽屉预览。',
  tags: ['图片', '批量'],
  fields: [
    { key: 'dir', label: '图片目录', type: 'dir', required: true },
    { key: 'brightness', label: '亮度 %', type: 'number', default: 110, width: 'half' },
    { key: 'contrast', label: '对比度 %', type: 'number', default: 110, width: 'half' }
  ],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    const br = Number(v.brightness)
    const ct = Number(v.contrast)
    if (!Number.isFinite(br) || br < 10 || br > 300) return { error: '亮度需为 10~300 的百分比' }
    if (!Number.isFinite(ct) || ct < 10 || ct > 300) return { error: '对比度需为 10~300 的百分比' }
    return {
      rows: [
        { label: '源目录', value: dir, copy: true },
        { label: '参数', value: `亮度 ${br}% / 对比度 ${ct}%` }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const br = Number(v.brightness)
    const ct = Number(v.contrast)
    if (!dir || !Number.isFinite(br) || !Number.isFinite(ct)) return INVALID_CODE
    return `"""批量亮度/对比度：${Number.isFinite(br) ? br : 100}% / ${Number.isFinite(ct) ? ct : 100}%。"""
from PIL import Image, ImageEnhance

${COLLECT(dir)}
for i, f in enumerate(files, 1):
    im = Image.open(f).convert("RGB")
    im = ImageEnhance.Brightness(im).enhance(${Number.isFinite(br) && br >= 10 ? br : 100} / 100)
    im = ImageEnhance.Contrast(im).enhance(${Number.isFinite(ct) && ct >= 10 ? ct : 100} / 100)
    out = f"enhanced_{i:03d}.png"
    im.save(out)
    print(f"{os.path.basename(f)} → {out}")
`
  }
}

// ---------------------------------------------------------------------------
// 9. 圆角与边框
// ---------------------------------------------------------------------------
export const roundedFrameSchema: InteractiveToolSchema = {
  id: 'interactive:rounded-frame',
  title: '圆角与边框',
  description: '单张图片加圆角（透明四角）与可选描边，输出 PNG。',
  tags: ['图片'],
  fields: [
    { key: 'file', label: '图片文件', type: 'file', required: true, accept: IMG_EXTS },
    { key: 'radius', label: '圆角半径(px)', type: 'number', default: 24, width: 'half' },
    { key: 'border', label: '描边宽度(px)', type: 'number', default: 0, width: 'half', help: '0 = 不加描边' },
    { key: 'borderColor', label: '描边颜色', type: 'text', default: '#333333', width: 'half', placeholder: '#333333' }
  ],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择图片文件' }
    const radius = Math.trunc(Number(v.radius ?? 24))
    if (!Number.isFinite(radius) || radius < 0 || radius > 500) return { error: '圆角半径需为 0~500 的整数' }
    const border = Math.trunc(Number(v.border ?? 0))
    if (!Number.isFinite(border) || border < 0 || border > 100) return { error: '描边宽度需为 0~100 的整数' }
    const color = str(v.borderColor ?? '#333333')
    if (!/^#[0-9a-fA-F]{6}$/.test(color)) return { error: '描边颜色需为 #RRGGBB' }
    return {
      rows: [
        { label: '源文件', value: file, copy: true },
        { label: '参数', value: `圆角 ${radius}px · 描边 ${border}px ${color}` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const radius = Math.trunc(Number(v.radius ?? 24))
    const border = Math.trunc(Number(v.border ?? 0))
    const color = str(v.borderColor ?? '#333333')
    if (!file || !/^#[0-9a-fA-F]{6}$/.test(color)) return INVALID_CODE
    return `"""圆角 + 描边（输出 PNG，透明四角）。"""
from PIL import Image, ImageDraw

im = Image.open(${JSON.stringify(file)}).convert("RGBA")
w, h = im.size
radius = ${Number.isFinite(radius) && radius >= 0 ? radius : 24}
border = ${Number.isFinite(border) && border >= 0 ? border : 0}
color = tuple(int("${color.replace('#', '')}"[i:i + 2], 16) for i in (0, 2, 4))

mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
im.putalpha(mask)
if border > 0:
    canvas = Image.new("RGBA", (w + border * 2, h + border * 2), color + (255,))
    canvas.paste(im, (border, border), im)
    im = canvas
im.save("rounded.png")
print(f"输出 rounded.png {im.size[0]}x{im.size[1]}")
`
  }
}

// ---------------------------------------------------------------------------
// 10. 图片信息报告
// ---------------------------------------------------------------------------
export const imageInfoSchema: InteractiveToolSchema = {
  id: 'interactive:image-info',
  title: '图片信息报告',
  description: '单张图片的格式/尺寸/模式/体积速览（含像素量与宽高比）。',
  tags: ['图片', '分析'],
  fields: [{ key: 'file', label: '图片文件', type: 'file', required: true, accept: IMG_EXTS }],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择图片文件' }
    return { rows: [{ label: '源文件', value: file, copy: true }] }
  },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return INVALID_CODE
    return `"""图片信息报告。"""
import os

from PIL import Image

im = Image.open(${JSON.stringify(file)})
w, h = im.size
size_bytes = os.path.getsize(${JSON.stringify(file)})
g = __import__("math").gcd(w, h)
print(f"格式: {im.format} | 模式: {im.mode}")
print(f"尺寸: {w}x{h}（宽高比 {w // g}:{h // g}）")
print(f"像素量: {w * h:,}")
print(f"体积: {size_bytes / 1024:.1f} KiB")
if getattr(im, "n_frames", 1) > 1:
    print(f"帧数: {im.n_frames}")
`
  }
}

// ---------------------------------------------------------------------------
// 11. Excel → CSV/JSON（openpyxl 只读）
// ---------------------------------------------------------------------------
export const excelExportSchema: InteractiveToolSchema = {
  id: 'interactive:excel-export',
  title: 'Excel → CSV/JSON',
  description: '读取工作簿首个工作表（或指定名称），导出为 CSV / JSON 文本（首行作表头）。',
  tags: ['Excel', '转换'],
  fields: [
    { key: 'file', label: '工作簿', type: 'file', required: true, accept: ['xlsx', 'xlsm'] },
    { key: 'sheet', label: '工作表名', type: 'text', width: 'half', placeholder: '留空 = 第一个' },
    {
      key: 'format',
      label: '导出格式',
      type: 'select',
      default: 'csv',
      width: 'half',
      options: [
        { value: 'csv', label: 'CSV' },
        { value: 'json', label: 'JSON' }
      ]
    }
  ],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择工作簿' }
    return {
      rows: [
        { label: '源文件', value: file, copy: true },
        { label: '工作表', value: str(v.sheet) || '（第一个）' },
        { label: '导出格式', value: str(v.format ?? 'csv').toUpperCase() }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const sheet = str(v.sheet)
    const fmt = str(v.format ?? 'csv')
    if (!file) return INVALID_CODE
    const load = sheet
      ? `wb = load_workbook(${JSON.stringify(file)}, read_only=True, data_only=True)\nws = wb[${JSON.stringify(sheet)}]`
      : `wb = load_workbook(${JSON.stringify(file)}, read_only=True, data_only=True)\nws = wb.active`
    return `"""Excel → ${fmt.toUpperCase()}（openpyxl 只读，首行作表头）。"""
import csv as _csv
import io
import json

from openpyxl import load_workbook

${load}
rows = [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
head, body = rows[0], rows[1:]
${
  fmt === 'json'
    ? `print(json.dumps([dict(zip(head, r)) for r in body], ensure_ascii=False, indent=2, default=str))`
    : `buf = io.StringIO()
w = _csv.writer(buf)
w.writerows(rows)
print(buf.getvalue())`
}
`
  }
}

// ---------------------------------------------------------------------------
// 12. CSV → Excel（openpyxl 写）
// ---------------------------------------------------------------------------
export const csvToExcelSchema: InteractiveToolSchema = {
  id: 'interactive:csv-excel',
  title: 'CSV → Excel',
  description: '把 CSV（首行表头）写成 .xlsx 工作簿，产物在抽屉下载。',
  tags: ['Excel', '转换'],
  fields: [
    { key: 'file', label: 'CSV 文件', type: 'file', required: true, accept: ['csv'] },
    { key: 'sheet', label: '工作表名', type: 'text', default: 'Sheet1', width: 'half' }
  ],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择 CSV 文件' }
    return {
      rows: [
        { label: '源文件', value: file, copy: true },
        { label: '工作表名', value: str(v.sheet ?? 'Sheet1') || 'Sheet1' }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const sheet = str(v.sheet ?? 'Sheet1') || 'Sheet1'
    if (!file) return INVALID_CODE
    return `"""CSV → Excel（openpyxl 写出）。"""
import csv

from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = ${JSON.stringify(sheet)}
with open(${JSON.stringify(file)}, newline="", encoding="utf-8-sig") as f:
    for row in csv.reader(f):
        ws.append(row)
wb.save("converted.xlsx")
print("已输出 converted.xlsx")
`
  }
}

// ---------------------------------------------------------------------------
// 13. PDF 文本提取（pypdf；默认前 5 页防巨型文档刷屏）
// ---------------------------------------------------------------------------
export const pdfExtractSchema: InteractiveToolSchema = {
  id: 'interactive:pdf-extract',
  title: 'PDF 文本提取',
  description: 'pypdf 抽取文本（默认前 5 页，可调 1~50），报告总页数与字符量。',
  tags: ['PDF'],
  fields: [
    { key: 'file', label: 'PDF 文件', type: 'file', required: true, accept: ['pdf'] },
    { key: 'pages', label: '页数上限', type: 'number', default: 5, width: 'half', help: '1~50' }
  ],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择 PDF 文件' }
    const pages = Math.trunc(Number(v.pages ?? 5))
    if (!Number.isFinite(pages) || pages < 1 || pages > 50) return { error: '页数上限需为 1~50 的整数' }
    return {
      rows: [
        { label: '源文件', value: file, copy: true },
        { label: '页数上限', value: String(pages) }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const pages = Math.trunc(Number(v.pages ?? 5))
    if (!file || !Number.isFinite(pages) || pages < 1) return INVALID_CODE
    return `"""PDF 文本提取（pypdf，前 ${Number.isFinite(pages) && pages <= 50 ? pages : 5} 页）。"""
from pypdf import PdfReader

r = PdfReader(${JSON.stringify(file)})
n = min(len(r.pages), ${Number.isFinite(pages) && pages <= 50 ? pages : 5})
texts = [r.pages[i].extract_text() or "" for i in range(n)]
total = sum(len(t) for t in texts)
print(f"总页数 {len(r.pages)}，已提取 {n} 页，共 {total} 字符")
print("-" * 40)
for i, t in enumerate(texts, 1):
    print(f"--- 第 {i} 页 ---")
    print(t)
`
  }
}

// ---------------------------------------------------------------------------
// 14. 图片转 PDF（目录批量合成一个多页 PDF）
// ---------------------------------------------------------------------------
export const imgToPdfSchema: InteractiveToolSchema = {
  id: 'interactive:img-to-pdf',
  title: '图片转 PDF',
  description: '目录内全部图片按文件名顺序合成一个多页 PDF（每图一页，RGB 白底）。',
  tags: ['图片', 'PDF'],
  fields: [{ key: 'dir', label: '图片目录', type: 'dir', required: true }],
  compute: (v) => {
    const dir = str(v.dir)
    if (!dir) return { error: '请选择图片目录' }
    return { rows: [{ label: '源目录', value: dir, copy: true }] }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return INVALID_CODE
    return `"""图片转 PDF（每图一页）。"""
from PIL import Image

${COLLECT(dir)}
pages = []
for f in files:
    im = Image.open(f)
    ${jpgGuard('im')}
    pages.append(im)
pages[0].save("out.pdf", save_all=True, append_images=pages[1:])
print(f"已输出 out.pdf：{len(pages)} 页")
`
  }
}

export const FILE_TOOL_SCHEMAS: InteractiveToolSchema[] = [
  batchResizeSchema,
  batchConvertSchema,
  batchCropSchema,
  batchWatermarkSchema,
  paletteSchema,
  gifExtractSchema,
  gifComposeSchema,
  batchEnhanceSchema,
  roundedFrameSchema,
  imageInfoSchema,
  excelExportSchema,
  csvToExcelSchema,
  pdfExtractSchema,
  imgToPdfSchema
]
