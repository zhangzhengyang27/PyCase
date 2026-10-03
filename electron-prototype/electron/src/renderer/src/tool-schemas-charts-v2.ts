// tool-schemas-charts-v2.ts：V2 图表扩展 ×12——直方图/热力图/3D 曲面/雷达/箱线/等高线/
// 面积/误差条/水平条形/极坐标玫瑰/散点密度/阶梯图。复用 V1 的模式（CSV → matplotlib → PNG）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const INVALID = '# 粘贴 CSV 数据后自动生成图表代码'
const PRELUDE = `import csv
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

const OUT = `fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

const TITLE_LINE = (v: Record<string, unknown>): string => `ax.set_title(${JSON.stringify(str(v.title ?? ''))})`

function base(
  title: string,
  description: string,
  tags: string[],
  fields: InteractiveToolSchema['fields'],
  body: (v: Record<string, unknown>) => string
): InteractiveToolSchema {
  return {
    id: `interactive:${title.replace(/\s+/g, '-').toLowerCase()}`,
    title,
    description,
    tags,
    fields,
    computeVia: 'sidecar',
    compute: (v) => {
      const data = str(v.data)
      const lines = data
        .trim()
        .split('\n')
        .filter((l) => l.trim())
      if (lines.length < 2) return { error: 'CSV 至少需要表头行 + 一行数据' }
      return { rows: [{ label: '数据行', value: String(lines.length - 1) }] }
    },
    pyCode: (v) => {
      const data = str(v.data)
      const lines = data
        .trim()
        .split('\n')
        .filter((l) => l.trim())
      if (lines.length < 2) return INVALID
      return PRELUDE + '\n' + `header, data_rows = parse_csv(${JSON.stringify(data)})\n` + body(v) + '\n' + OUT
    }
  }
}

const DATA_FIELD = { key: 'data', label: '数据（CSV）', type: 'textarea' as const, required: true }
const TITLE_FIELD = { key: 'title', label: '标题', type: 'text' as const, default: '', width: 'half' as const }

// ---------------------------------------------------------------------------
export const histChartSchema = base(
  '直方图',
  '数值分布直方图：第二列数值自动分箱。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD, { key: 'bins', label: '分箱数', type: 'number', default: 20, width: 'half' }],
  (v) => {
    const bins = Math.max(2, Math.min(200, Math.trunc(Number(v.bins ?? 20)) || 20))
    return `values = [float(r[1]) for r in data_rows]
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(values, bins=${bins}, edgecolor="white", alpha=0.8)
${TITLE_LINE(v)}`
  }
)

export const heatmapChartSchema = base(
  '热力图',
  '行列标签热力图：数据首行为列标签，首列为行标签（数值取浮点）。',
  ['图表'],
  [
    DATA_FIELD,
    TITLE_FIELD,
    {
      key: 'cmap',
      label: '色系',
      type: 'text',
      default: 'YlOrRd',
      width: 'half',
      placeholder: 'YlOrRd / viridis / coolwarm'
    }
  ],
  (v) => {
    const cmap = str(v.cmap ?? 'YlOrRd').replace(/[^a-zA-Z0-9_]/g, '') || 'YlOrRd'
    return `import numpy as np

labels = [r[0] for r in data_rows]
mat = np.array([[float(c) for c in r[1:]] for r in data_rows])
col_labels = header[1:]

fig, ax = plt.subplots(figsize=(max(6, len(col_labels) * 1.2), max(4, len(labels) * 0.6)))
im = ax.imshow(mat, cmap="${cmap}", aspect="auto")
ax.set_xticks(range(len(col_labels)), col_labels, rotation=45, ha="right")
ax.set_yticks(range(len(labels)), labels)
fig.colorbar(im, ax=ax)
${TITLE_LINE(v)}`
  }
)

export const radarChartSchema = base(
  '雷达图',
  '多指标雷达图：数据首列为指标名，后续各列为一个实体（表头做图例）。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD, { key: 'fill', label: '填充区域', type: 'checkbox', default: true, width: 'half' }],
  (v) => {
    const fill = v.fill === true
    return `import numpy as np

cats = [r[0] for r in data_rows]
series = list(zip(*[(float(c) for c in r[1:]) for r in data_rows]))
names = header[1:]
angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
angles += angles[:1]

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
for i, (vals, name) in enumerate(zip(series, names)):
    vals = list(vals) + [vals[0]]
    ax.plot(angles, vals, label=name)
    ${fill ? 'ax.fill(angles, vals, alpha=0.15)' : ''}
ax.set_xticks(angles[:-1], cats)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
${TITLE_LINE(v)}`
  }
)

export const boxPlotSchema = base(
  '箱线图',
  '多组箱线图：首列分组标签，第二列数值（按组聚合绘制）。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD],
  (v) => `from collections import defaultdict

groups: dict = defaultdict(list)
for r in data_rows:
    groups[r[0]].append(float(r[1]))
labels = sorted(groups.keys())
data = [groups[k] for k in labels]
fig, ax = plt.subplots(figsize=(8, 5))
ax.boxplot(data, tick_labels=labels)
${TITLE_LINE(v)}`
)

export const areaChartSchema = base(
  '面积图',
  '堆叠面积图：首列 X 轴，后续各列为一个系列。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD],
  (v) => `columns = list(zip(*data_rows))
x = columns[0]
series = [[float(c) for c in col] for col in columns[1:]]
fig, ax = plt.subplots(figsize=(8, 5))
ax.stackplot(x, series, labels=header[1:])
ax.legend(loc="upper left")
${TITLE_LINE(v)}`
)

export const errBarChartSchema = base(
  '误差条图',
  '柱状图 + 误差条：首列标签，第二列均值，第三列标准差。',
  ['图表'],
  [{ key: 'data', label: '数据（CSV：标签,均值,标准差）', type: 'textarea', required: true }, TITLE_FIELD],
  (v) => `import numpy as np

labels = [r[0] for r in data_rows]
means = [float(r[1]) for r in data_rows]
stds = [float(r[2]) if len(r) > 2 else 0 for r in data_rows]
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(labels, means, yerr=stds, capsize=5, color="#6366f1", alpha=0.8)
${TITLE_LINE(v)}`
)

export const hBarChartSchema = base(
  '水平条形图',
  '水平条形排行榜：按数值降序排列。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD],
  (v) => `data_rows.sort(key=lambda r: float(r[1]), reverse=True)
labels = [r[0] for r in data_rows]
values = [float(r[1]) for r in data_rows]
fig, ax = plt.subplots(figsize=(8, max(4, len(labels) * 0.4)))
ax.barh(labels[::-1], values[::-1], color="#10b981")
${TITLE_LINE(v)}`
)

export const polarRoseSchema = base(
  '极坐标玫瑰',
  '极坐标玫瑰图：首列方向标签，第二列数值。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD],
  (v) => `import numpy as np

cats = [r[0] for r in data_rows]
vals = [float(r[1]) for r in data_rows]
angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False)
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.bar(angles, vals, width=2 * np.pi / len(cats), alpha=0.7)
ax.set_xticks(angles, cats)
${TITLE_LINE(v)}`
)

export const scatterDensitySchema = base(
  '散点密度图',
  '大数据量散点 + 密度着色（hexbin 六角分箱）。',
  ['图表'],
  [
    { key: 'data', label: '数据（CSV：x,y）', type: 'textarea', required: true },
    TITLE_FIELD,
    { key: 'gridsize', label: '分箱数', type: 'number', default: 30, width: 'half' }
  ],
  (v) => {
    const gs = Math.max(5, Math.min(100, Math.trunc(Number(v.gridsize ?? 30)) || 30))
    return `import numpy as np

xs = [float(r[0]) for r in data_rows]
ys = [float(r[1]) for r in data_rows]
fig, ax = plt.subplots(figsize=(8, 6))
hb = ax.hexbin(xs, ys, gridsize=${gs}, cmap="viridis", mincnt=1)
fig.colorbar(hb, ax=ax, label="count")
${TITLE_LINE(v)}`
  }
)

export const stepChartSchema = base(
  '阶梯图',
  '阶梯折线图（where=post/pre/mid 可选）。',
  ['图表'],
  [
    DATA_FIELD,
    TITLE_FIELD,
    {
      key: 'where',
      label: '阶梯位置',
      type: 'select',
      default: 'post',
      width: 'half',
      options: [
        { value: 'post', label: 'post' },
        { value: 'pre', label: 'pre' },
        { value: 'mid', label: 'mid' }
      ]
    }
  ],
  (v) => {
    const where = ['post', 'pre', 'mid'].includes(str(v.where)) ? str(v.where) : 'post'
    return `columns = list(zip(*data_rows))
x = columns[0]
ys = [[float(c) for c in col] for col in columns[1:]]
fig, ax = plt.subplots(figsize=(8, 5))
for i, y in enumerate(ys):
    ax.step(x, y, where="${where}", label=header[i + 1] if i + 1 < len(header) else f"y{i}")
ax.legend()
${TITLE_LINE(v)}`
  }
)

export const contourChartSchema = base(
  '等高线图',
  '等高线图：数据为 X 值序列网格（行列均数值，绘制多级等高线）。',
  ['图表'],
  [DATA_FIELD, TITLE_FIELD, { key: 'levels', label: '等高线级数', type: 'number', default: 10, width: 'half' }],
  (v) => {
    const levels = Math.max(3, Math.min(50, Math.trunc(Number(v.levels ?? 10)) || 10))
    return `import numpy as np

mat = np.array([[float(c) for c in r[1:]] for r in data_rows])
fig, ax = plt.subplots(figsize=(8, 6))
cs = ax.contourf(mat, levels=${levels}, cmap="coolwarm")
fig.colorbar(cs, ax=ax)
${TITLE_LINE(v)}`
  }
)

export const W2v2_SCHEMAS: InteractiveToolSchema[] = [
  histChartSchema,
  heatmapChartSchema,
  radarChartSchema,
  boxPlotSchema,
  areaChartSchema,
  errBarChartSchema,
  hBarChartSchema,
  polarRoseSchema,
  scatterDensitySchema,
  stepChartSchema,
  contourChartSchema
]
