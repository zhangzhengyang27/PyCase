// tool-schemas-charts.ts：V1 图表生成器 ×4——折线/柱状/散点/饼图。
// 模式：CSV 数据 textarea → pyCode 产 matplotlib 脚本 → sidecar 运行 → PNG 进抽屉预览。
// 每个脚本自含 CJK 字体设置（PingFang SC / 微软雅黑 / SimHei 依平台回退）。
// 只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const INVALID = '# 粘贴 CSV 数据后自动生成图表代码'

// ---------------------------------------------------------------------------
// 共享 matplotlib 序章：CJK 字体 + CSV 解析
// ---------------------------------------------------------------------------
const MPL_PRELUDE = `import csv
import io

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei", "Arial Unicode MS",
]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

def parse_csv(text):
    rows = list(csv.reader(io.StringIO(text.strip())))
    return rows[0], rows[1:]
`

/** 校验 CSV 至少两列两行，返回 header 行 */
function validateCsv(text: string, minCols = 2): string[] | string {
  const lines = text
    .trim()
    .split('\n')
    .filter((l) => l.trim())
  if (lines.length < 2) return 'CSV 至少需要表头行 + 一行数据'
  const cols = lines[0]!.split(',').length
  if (cols < minCols) return `至少需要 ${minCols} 列数据`
  return lines[0]!.split(',').map((c) => c.trim())
}

// ---------------------------------------------------------------------------
// 1. 折线图
// ---------------------------------------------------------------------------
export const lineChartSchema: InteractiveToolSchema = {
  id: 'interactive:chart-line',
  title: '折线图',
  description: '多系列折线图：首列 X 轴，后续列为 Y 系列（表头做图例）。支持网格/标记/线宽。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首列 X 轴）',
      type: 'textarea',
      required: true,
      placeholder: '月份,系列A,系列B\n1月,10,20\n2月,15,25'
    },
    { key: 'title', label: '标题', type: 'text', default: '', width: 'half' },
    { key: 'grid', label: '显示网格', type: 'checkbox', default: true },
    { key: 'marker', label: '数据点标记', type: 'checkbox', default: true },
    { key: 'linewidth', label: '线宽', type: 'number', default: 2, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const data = str(v.data)
    const err = validateCsv(data)
    if (typeof err === 'string') return { error: err }
    return {
      rows: [
        { label: '系列数', value: String(err.length - 1) },
        { label: '数据行', value: String(data.trim().split('\n').length - 1) }
      ]
    }
  },
  pyCode: (v) => {
    const data = str(v.data)
    const err = validateCsv(data)
    if (typeof err === 'string') return INVALID
    const marker = v.marker === true ? '"o"' : 'None'
    const lw = Math.max(0.5, Number(v.linewidth ?? 2) || 2)
    const title = str(v.title)
    const grid = v.grid !== false
    return `${MPL_PRELUDE}
header, data_rows = parse_csv(${JSON.stringify(data)})
columns = list(zip(*data_rows))
x = columns[0]

fig, ax = plt.subplots(figsize=(8, 5))
for i in range(1, len(header)):
    ax.plot(x, [float(c) for c in columns[i]],
            marker=${marker}, linewidth=${lw}, label=header[i])

ax.set_title(${JSON.stringify(str(v.title ?? ''))})
ax.legend()
${grid ? 'ax.grid(True, alpha=0.3)' : 'ax.grid(False)'}
fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True},
                           {"label": "系列", "value": str(len(header) - 1)}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 2. 柱状图
// ---------------------------------------------------------------------------
export const barChartSchema: InteractiveToolSchema = {
  id: 'interactive:chart-bar',
  title: '柱状图',
  description: '柱状图：首列分类标签，第二列数值。支持颜色/水平方向。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首列分类，第二列数值）',
      type: 'textarea',
      required: true,
      placeholder: '类别,数值\n苹果,120\n香蕉,85'
    },
    { key: 'title', label: '标题', type: 'text', default: '', width: 'half' },
    { key: 'color', label: '颜色', type: 'text', default: '#3b82f6', width: 'half', placeholder: '#3b82f6' },
    { key: 'horizontal', label: '水平柱状', type: 'checkbox' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const data = str(v.data)
    const err = validateCsv(data, 2)
    if (typeof err === 'string') return { error: err }
    return { rows: [{ label: '数据行', value: String(data.trim().split('\n').length - 1) }] }
  },
  pyCode: (v) => {
    const data = str(v.data)
    const err = validateCsv(data, 2)
    if (typeof err === 'string') return INVALID
    const color = /^#[0-9a-fA-F]{6}$/.test(str(v.color)) ? str(v.color) : '#3b82f6'
    const horiz = v.horizontal === true
    const plotCall = horiz ? `ax.barh(labels, values, color="${color}")` : `ax.bar(labels, values, color="${color}")`
    return `${MPL_PRELUDE}
header, data_rows = parse_csv(${JSON.stringify(data)})
labels = [r[0] for r in data_rows]
values = [float(r[1]) for r in data_rows]

fig, ax = plt.subplots(figsize=(8, 5))
${plotCall}
ax.set_title(${JSON.stringify(str(v.title ?? ''))})
fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True},
                           {"label": "类别数", "value": str(len(labels))}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 3. 散点图
// ---------------------------------------------------------------------------
export const scatterChartSchema: InteractiveToolSchema = {
  id: 'interactive:chart-scatter',
  title: '散点图',
  description: '散点图：首列 X 值，第二列 Y 值。支持点大小/透明度/颜色。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首列 X，第二列 Y）',
      type: 'textarea',
      required: true,
      placeholder: 'x,y\n1,3\n2,7\n3,2'
    },
    { key: 'title', label: '标题', type: 'text', default: '', width: 'half' },
    { key: 'color', label: '颜色', type: 'text', default: '#ef4444', width: 'half', placeholder: '#ef4444' },
    { key: 'size', label: '点大小', type: 'number', default: 40, width: 'half' },
    { key: 'alpha', label: '透明度', type: 'number', default: 0.7, width: 'half', help: '0~1' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const data = str(v.data)
    const err = validateCsv(data, 2)
    if (typeof err === 'string') return { error: err }
    return { rows: [{ label: '数据点', value: String(data.trim().split('\n').length - 1) }] }
  },
  pyCode: (v) => {
    const data = str(v.data)
    const err = validateCsv(data, 2)
    if (typeof err === 'string') return INVALID
    const color = /^#[0-9a-fA-F]{6}$/.test(str(v.color)) ? str(v.color) : '#ef4444'
    const size = Math.max(5, Number(v.size ?? 40) || 40)
    const alpha = Math.min(1, Math.max(0.1, Number(v.alpha ?? 0.7) || 0.7))
    return `${MPL_PRELUDE}
header, data_rows = parse_csv(${JSON.stringify(data)})
xs = [float(r[0]) for r in data_rows]
ys = [float(r[1]) for r in data_rows]

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(xs, ys, s=${size}, c="${color}", alpha=${alpha}, edgecolors="white", linewidths=0.5)
ax.set_title(${JSON.stringify(str(v.title ?? ''))})
fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True},
                           {"label": "数据点", "value": str(len(xs))}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 4. 饼图
// ---------------------------------------------------------------------------
export const pieChartSchema: InteractiveToolSchema = {
  id: 'interactive:chart-pie',
  title: '饼图',
  description: '饼图/环形图：首列标签，第二列数值。支持百分比标注/起始角度/环形模式。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首列标签，第二列数值）',
      type: 'textarea',
      required: true,
      placeholder: '类别,数量\n苹果,35\n香蕉,25\n橙子,40'
    },
    { key: 'title', label: '标题', type: 'text', default: '', width: 'half' },
    { key: 'donut', label: '环形模式', type: 'checkbox', width: 'half' },
    { key: 'startangle', label: '起始角度', type: 'number', default: 90, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const data = str(v.data)
    const err = validateCsv(data, 2)
    if (typeof err === 'string') return { error: err }
    return { rows: [{ label: '扇区数', value: String(data.trim().split('\n').length - 1) }] }
  },
  pyCode: (v) => {
    const data = str(v.data)
    const err = validateCsv(data, 2)
    if (typeof err === 'string') return INVALID
    const donut = v.donut === true ? ', wedgeprops={"width": 0.45}' : ''
    const sa = Math.max(0, Math.min(360, Number(v.startangle ?? 90) || 90))
    return `${MPL_PRELUDE}
header, data_rows = parse_csv(${JSON.stringify(data)})
labels = [r[0] for r in data_rows]
values = [float(r[1]) for r in data_rows]

fig, ax = plt.subplots(figsize=(7, 7))
ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=${sa}${donut})
ax.set_title(${JSON.stringify(str(v.title ?? ''))})
fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True},
                           {"label": "扇区数", "value": str(len(labels))}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const CHART_SCHEMAS: InteractiveToolSchema[] = [
  lineChartSchema,
  barChartSchema,
  scatterChartSchema,
  pieChartSchema
]
