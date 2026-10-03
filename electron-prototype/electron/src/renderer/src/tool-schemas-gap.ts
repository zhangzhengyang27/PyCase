// tool-schemas-charts-gap.ts：V5 图表缺口补齐 ×10——3D 系/子图布局/双轴/对数/词云/韦恩/甘特/树状图。
// 形态与 V1/V2 相同：CSV/文本输入 → matplotlib → PNG 预览。
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
// 1. 3D 曲面图
// ---------------------------------------------------------------------------
export const surface3dSchema = base(
  '3D 曲面图',
  '三维曲面：数据为 Z 值网格（行为 y、列为 x）。',
  ['图表', '3D'],
  [DATA_FIELD, TITLE_FIELD, { key: 'cmap', label: '色系', type: 'text', default: 'viridis', width: 'half' }],
  (v) => {
    const cmap = str(v.cmap ?? 'viridis').replace(/[^a-zA-Z0-9_]/g, '') || 'viridis'
    return `import numpy as np

mat = np.array([[float(c) for c in r[1:]] for r in data_rows], dtype=float)
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
X, Y = np.meshgrid(np.arange(mat.shape[1]), np.arange(mat.shape[0]))
surf = ax.plot_surface(X, Y, mat, cmap="${cmap}", edgecolor="k", linewidth=0.2)
fig.colorbar(surf, ax=ax, shrink=0.6)
${TITLE_LINE(v)}`
  }
)

// ---------------------------------------------------------------------------
// 2. 3D 散点图
// ---------------------------------------------------------------------------
export const scatter3dSchema = base(
  '3D 散点图',
  '三维散点：数据列依次为 x,y,z（第四列可选为大小）。',
  ['图表', '3D'],
  [DATA_FIELD, TITLE_FIELD, { key: 'color', label: '颜色', type: 'text', default: '#2563eb', width: 'half' }],
  (v) => {
    const color = /^#[0-9a-fA-F]{6}$/.test(str(v.color)) ? str(v.color) : '#2563eb'
    return `xs = [float(r[0]) for r in data_rows]
ys = [float(r[1]) for r in data_rows]
zs = [float(r[2]) for r in data_rows]

fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(xs, ys, zs, c="${color}", s=40, edgecolors="white")
ax.set_xlabel(header[0])
ax.set_ylabel(header[1])
ax.set_zlabel(header[2])
${TITLE_LINE(v)}`
  }
)

// ---------------------------------------------------------------------------
// 3. 子图布局
// ---------------------------------------------------------------------------
export const subplotsSchema = base(
  '子图布局',
  '多子图组合：每行一条子图数据（首列为 X），自动纵向排列共享标题区。',
  ['图表', '布局'],
  [DATA_FIELD, TITLE_FIELD],
  (v) => `columns = list(zip(*data_rows))
x = columns[0]
series = columns[1:]
n = len(series)
fig, axes = plt.subplots(n, 1, figsize=(8, 3 * n), squeeze=False)
for i, (ax, col) in enumerate(zip(axes.flat, series)):
    ax.plot(x, [float(c) for c in col])
    ax.set_ylabel(header[i + 1])
${TITLE_LINE(v)}`
)

// ---------------------------------------------------------------------------
// 4. 双轴对比
// ---------------------------------------------------------------------------
export const dualAxisSchema = base(
  '双轴对比',
  '双 Y 轴组合图：第一系列用左轴，第二系列用右轴。',
  ['图表', '布局'],
  [DATA_FIELD, TITLE_FIELD, { key: 'secondColor', label: '右轴颜色', type: 'text', default: '#ef4444', width: 'half' }],
  (v) => {
    const c2 = /^#[0-9a-fA-F]{6}$/.test(str(v.secondColor)) ? str(v.secondColor) : '#ef4444'
    return `columns = list(zip(*data_rows))
x = columns[0]
fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(x, [float(c) for c in columns[1]], color="#3b82f6", label=header[1])
ax1.set_ylabel(header[1], color="#3b82f6")
ax2 = ax1.twinx()
ax2.plot(x, [float(c) for c in columns[2]], color="${c2}", label=header[2])
ax2.set_ylabel(header[2], color="${c2}")
${TITLE_LINE(v)}`
  }
)

// ---------------------------------------------------------------------------
// 5. 对数坐标
// ---------------------------------------------------------------------------
export const logScaleSchema = base(
  '对数坐标图',
  'Y 轴对数坐标折线（适合跨数量级数据）。',
  ['图表', '布局'],
  [DATA_FIELD, TITLE_FIELD],
  (v) => `columns = list(zip(*data_rows))
x = columns[0]
fig, ax = plt.subplots(figsize=(8, 5))
for i, col in enumerate(columns[1:], 1):
    ax.plot(x, [float(c) for c in col], marker="o", label=header[i])
ax.set_yscale("log")
ax.legend()
ax.grid(True, alpha=0.3)
${TITLE_LINE(v)}`
)

// ---------------------------------------------------------------------------
// 6. 词云图（wordcloud 已装）
// ---------------------------------------------------------------------------
export const wordcloudSchema: InteractiveToolSchema = {
  id: 'interactive:wordcloud-chart',
  title: '词云图',
  description: '词频列表 → 词云 PNG（wordcloud；每行「词,权重」，权重越大字越大）。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '词频（CSV：词,权重）',
      type: 'textarea',
      required: true,
      placeholder: 'Python,100\n图表,60\n数据,80'
    },
    TITLE_FIELD,
    { key: 'bg', label: '背景色', type: 'text', default: '#ffffff', width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.data).trim()
      ? {
          rows: [
            {
              label: '词条数',
              value: String(
                str(v.data)
                  .split('\n')
                  .filter((l) => l.trim()).length
              )
            }
          ]
        }
      : { error: '请粘贴词频数据' },
  pyCode: (v) => {
    const data = str(v.data)
    if (!data.trim()) return INVALID
    const bg = /^#[0-9a-fA-F]{6}$/.test(str(v.bg ?? '#ffffff')) ? str(v.bg) : '#ffffff'
    return `"""词云图（wordcloud + matplotlib）。"""
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["PingFang SC", "Microsoft YaHei", "SimHei"]
import matplotlib.pyplot as plt
from wordcloud import WordCloud

freq = {}
for line in ${JSON.stringify(data)}.splitlines():
    if "," in line:
        k, _, w = line.partition(",")
        freq[k.strip()] = float(w or 1)

wc = WordCloud(font_path=None, width=800, height=500, background_color="${bg}",
               max_words=200, regexp=r".+")
try:
    wc.generate_from_frequencies(freq)
except ValueError:
    raise SystemExit("词频数据不足")
wc.to_file("chart.png")
fig, ax = plt.subplots(figsize=(8, 5))
ax.imshow(plt.imread("chart.png"))
ax.axis("off")
${TITLE_LINE(v)}
${OUT}`
  }
}

// ---------------------------------------------------------------------------
// 7. 韦恩图（matplotlib_venn 已装；两/三集合）
// ---------------------------------------------------------------------------
export const vennSchema: InteractiveToolSchema = {
  id: 'interactive:venn',
  title: '韦恩图',
  description: '两集合或三集合交叠图：每行「集合名,元素数」（2-3 行）。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '集合规模（CSV：名称,元素数，2-3 行）',
      type: 'textarea',
      required: true,
      placeholder: '集合A,18\n集合B,12\n共有,7'
    },
    TITLE_FIELD
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const rows = str(v.data)
      .split('\n')
      .filter((l) => l.trim())
    if (rows.length < 2 || rows.length > 3) return { error: '韦恩图支持 2~3 个集合' }
    return { rows: [{ label: '集合数', value: String(rows.length) }] }
  },
  pyCode: (v) => {
    const data = str(v.data)
    const rows = data.split('\n').filter((l) => l.trim())
    if (rows.length < 2 || rows.length > 3) return '# 韦恩图支持 2~3 个集合'
    const vals = rows.map((r) => Number(r.split(',')[1] ?? 0))
    const names = rows.map((r) => r.split(',')[0] ?? '')
    const imp =
      rows.length === 2
        ? 'from matplotlib_venn import venn2 as venn\nvenn_fn = venn2\nsubset = (vals[0], vals[1], vals[2])'
        : 'from matplotlib_venn import venn3 as venn_fn\nsubset = (vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6])'
    return `"""韦恩图（matplotlib_venn）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

vals = [${vals.join(', ')}]
names = ${JSON.stringify(names)}
${imp}

fig, ax = plt.subplots(figsize=(6, 6))
venn_fn(subset=subset, set_labels=names, ax=ax)
${TITLE_LINE(v)}
${OUT}`
  }
}

// ---------------------------------------------------------------------------
// 8. 甘特图（broken_barh）
// ---------------------------------------------------------------------------
export const ganttSchema = base(
  '甘特图',
  '任务时间线：每行「任务,开始(天),持续(天)」。',
  ['图表'],
  [
    {
      key: 'data',
      label: '任务（CSV：任务,开始,持续）',
      type: 'textarea',
      required: true,
      placeholder: '需求分析,0,3\n开发,2,7\n测试,7,3'
    },
    TITLE_FIELD
  ],
  (v) => {
    return `tasks = []
for r in data_rows:
    tasks.append((r[0], float(r[1] or 0), float(r[2] or 0)))
tasks.sort(key=lambda t: t[1])
fig, ax = plt.subplots(figsize=(8, max(4, len(tasks) * 0.5)))
for i, (name, start, dur) in enumerate(tasks):
    ax.broken_barh([(start, dur)], (i - 0.35, 0.7), color="#3b82f6", alpha=0.85)
    ax.text(start + dur / 2, i, name, ha="center", va="center", color="white", fontsize=9)
ax.set_yticks(range(len(tasks)), [t[0] for t in tasks])
ax.set_xlabel("时间（天）")
${TITLE_LINE(v)}`
  }
)

// ---------------------------------------------------------------------------
// 9. 系统树状图（scipy dendrogram；scipy 已装）
// ---------------------------------------------------------------------------
export const dendrogramSchema: InteractiveToolSchema = {
  id: 'interactive:dendrogram',
  title: '系统树状图',
  description: '层次聚类树状图：数据矩阵（每行一个样本，列为特征，欧氏距离+最短连接）。',
  tags: ['图表', '统计'],
  fields: [DATA_FIELD, TITLE_FIELD],
  compute: (v) =>
    str(v.data).trim()
      ? {
          rows: [
            {
              label: '样本数',
              value: String(
                str(v.data)
                  .split('\n')
                  .filter((l) => l.trim()).length
              )
            }
          ]
        }
      : { error: '请粘贴数据' },
  pyCode: (v) => {
    const data = str(v.data)
    if (!data.trim()) return INVALID
    return `"""系统树状图（scipy 层次聚类）。"""
import json

import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage

mat = np.array([[float(c) for c in r[1:]] for r in data_rows], dtype=float)
labels = [r[0] for r in data_rows]
Z = linkage(mat, method="single")
fig, ax = plt.subplots(figsize=(9, 5))
dendrogram(Z, labels=labels, ax=ax)
${TITLE_LINE(v)}
${OUT}`
  }
}

// ---------------------------------------------------------------------------
// 10. 图片批量下载器（爬虫缺 1）
// ---------------------------------------------------------------------------
export const batchImageDownloadSchema: InteractiveToolSchema = {
  id: 'interactive:image-downloader',
  title: '图片批量下载',
  description: 'URL 列表（每行一个图片地址）批量下载到运行工作区，产物进抽屉预览（需联网）。',
  tags: ['网络', '爬虫'],
  fields: [
    {
      key: 'urls',
      label: '图片 URL（每行一个）',
      type: 'textarea',
      required: true,
      placeholder: 'https://…/a.png\nhttps://…/b.jpg'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const urls = str(v.urls)
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    if (!urls.length) return { error: '请输入至少一个图片 URL' }
    return { rows: [{ label: 'URL 数', value: String(urls.length) }] }
  },
  pyCode: (v) => {
    const urls = str(v.urls)
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    if (!urls.length) return '# 输入图片 URL 后自动生成代码'
    return `"""图片批量下载（requests 流式，失败行跳过并报告）。"""
import json

import requests

urls = ${JSON.stringify(urls)}
ok = fail = 0
for i, u in enumerate(urls, 1):
    try:
        resp = requests.get(u, timeout=20, headers={"User-Agent": "PyCase/1.0"})
        resp.raise_for_status()
        ext = ".png" if "png" in resp.headers.get("content-type", "") else ".jpg"
        name = f"download_{i:03d}{ext}"
        with open(name, "wb") as f:
            f.write(resp.content)
        ok += 1
        print(f"OK   {u} → {name}")
    except Exception as e:
        fail += 1
        print(f"FAIL {u}: {e}")
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": f"{ok}/{ok + fail}", "unit": "下载成功"}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const GAP_SCHEMAS: InteractiveToolSchema[] = [
  surface3dSchema,
  scatter3dSchema,
  subplotsSchema,
  dualAxisSchema,
  logScaleSchema,
  wordcloudSchema,
  vennSchema,
  ganttSchema,
  dendrogramSchema,
  batchImageDownloadSchema
]
