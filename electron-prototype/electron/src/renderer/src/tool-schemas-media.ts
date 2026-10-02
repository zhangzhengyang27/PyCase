// tool-schemas-media.ts：B 档文件管道试点——图片缩放。
// 文件管道形态：ToolField 的 file 字段经 pickFile 桥选真实文件（值为绝对路径），
// pyCode 产物在 sidecar adhoc 工作区运行时按路径读取源文件、把产物写到 CWD，
// sidecar 的 run_images 扫描把产物图推回抽屉预览（CodeDrawer 内下载）。
// 依赖 Pillow（共享 venv 已装）。只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const INVALID_CODE = '# 选择图片文件后自动生成代码'
const str = (v: unknown): string => String(v ?? '')

export const imageResizeSchema: InteractiveToolSchema = {
  id: 'interactive:image-resize',
  title: '图片缩放',
  description: '选一张本机图片，按长边上限等比缩放（只缩不放），产物在抽屉预览并可下载。Pillow 真实运行。',
  tags: ['图片', '文件管道'],
  fields: [
    { key: 'file', label: '图片文件', type: 'file', required: true, accept: ['png', 'jpg', 'jpeg', 'webp', 'bmp'] },
    { key: 'maxSide', label: '长边上限(px)', type: 'number', default: 1024, width: 'half', help: '等比缩放，只缩不放' },
    {
      key: 'format',
      label: '输出格式',
      type: 'select',
      default: 'png',
      width: 'half',
      options: [
        { value: 'png', label: 'PNG（无损）' },
        { value: 'jpg', label: 'JPG（体积小，透明底转白）' }
      ]
    }
  ],
  compute: (v) => {
    const file = str(v.file)
    if (!file) return { error: '请选择图片文件' }
    const maxSide = Math.trunc(Number(v.maxSide))
    if (!Number.isFinite(maxSide) || maxSide < 16 || maxSide > 20000) return { error: '长边上限需为 16~20000 的整数' }
    const format = str(v.format ?? 'png')
    return {
      rows: [
        { label: '源文件', value: file, copy: true },
        { label: '长边上限', value: `${maxSide} px` },
        { label: '输出格式', value: format.toUpperCase() }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const maxSide = Math.trunc(Number(v.maxSide))
    const fmt = str(v.format ?? 'png')
    if (!file || !Number.isFinite(maxSide) || maxSide < 16) return INVALID_CODE
    return `"""图片缩放：长边上限 ${maxSide}px（thumbnail 等比、只缩不放）。"""
from PIL import Image

im = Image.open(${JSON.stringify(file)})
before = im.size
im.thumbnail((${maxSide}, ${maxSide}))
out = "resized.${fmt}"
if "${fmt}" == "jpg" and im.mode in ("RGBA", "P"):
    im = im.convert("RGB")
if "${fmt}" == "jpg":
    im.save(out, quality=90)
else:
    im.save(out)
print(f"输出 {out}: {im.size[0]}x{im.size[1]}（原图 {before[0]}x{before[1]}）")
`
  }
}

export const MEDIA_SCHEMAS: InteractiveToolSchema[] = [imageResizeSchema]
