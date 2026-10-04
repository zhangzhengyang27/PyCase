// tool-schemas-charts-gap.ts：V5 图表缺口补齐 ×10——3D 系/子图布局/双轴/对数/词云/韦恩/甘特/树状图。
// 形态与 V1/V2 相同：CSV/文本输入 → matplotlib → PNG 预览。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const INVALID = '# 粘贴 CSV 数据后自动生成图表代码'
const PRELUDE = `import csv
import io
import json

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
  body: (v: Record<string, unknown>) => string,
  /** 标题尾巴：默认写到当前 ax；多子图页传 suptitle 版本 */
  tail?: (v: Record<string, unknown>) => string
): InteractiveToolSchema {
  const tailFn = tail ?? TITLE_LINE
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
      return (
        PRELUDE +
        '\n' +
        `header, data_rows = parse_csv(${JSON.stringify(data)})\n` +
        body(v) +
        '\n' +
        tailFn(v) +
        '\n' +
        OUT
      )
    }
  }
}

const DATA_FIELD = {
  key: 'data',
  label: '数据（CSV）',
  type: 'textarea' as const,
  required: true,
  placeholder: 'x,y\n1,2\n2,4\n3,9\n4,16'
}
const TITLE_FIELD = { key: 'title', label: '标题', type: 'text' as const, default: '', width: 'half' as const }

// ---------------------------------------------------------------------------
// 1. 3D 曲面图
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// 2. 3D 散点图
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// 3. 子图布局
// ---------------------------------------------------------------------------
export const subplotsSchema = base(
  '子图布局',
  '多子图组合：每行一条子图数据（首列为 X），自动纵向排列共享标题区。',
  ['图表', '布局'],
  [DATA_FIELD, TITLE_FIELD],
  (_v) => `columns = list(zip(*data_rows))
x = columns[0]
series = columns[1:]
n = len(series)
fig, axes = plt.subplots(n, 1, figsize=(8, 3 * n), squeeze=False)
for i, (ax, col) in enumerate(zip(axes.flat, series)):
    ax.plot(x, [float(c) for c in col])
    ax.set_ylabel(header[i + 1])`,
  (v) => `fig.suptitle(${JSON.stringify(str(v.title ?? ''))})`
)

// ---------------------------------------------------------------------------
// 4. 双轴对比
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// 5. 对数坐标
// ---------------------------------------------------------------------------

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
import json

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
  description:
    'matplotlib_venn 区域计数：2 集合填 3 行「名称,元素数」（仅A/仅B/交集）；3 集合填 7 行（仅A/仅B/仅C/AB/AC/BC/ABC）。',
  tags: ['图表'],
  fields: [
    {
      key: 'data',
      label: '区域元素数（CSV：名称,数量；2 集合 3 行 / 3 集合 7 行）',
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
    if (rows.length !== 3 && rows.length !== 7)
      return { error: '2 集合需 3 行（仅A/仅B/交集），3 集合需 7 行（仅A/仅B/仅C/AB/AC/BC/ABC）' }
    return { rows: [{ label: '集合数', value: rows.length === 3 ? '2' : '3' }] }
  },
  pyCode: (v) => {
    const data = str(v.data)
    const rows = data.split('\n').filter((l) => l.trim())
    if (rows.length !== 3 && rows.length !== 7) return '# 2 集合需 3 行 / 3 集合需 7 行（区域元素数）'
    const vals = rows.map((r) => Number(r.split(',')[1] ?? 0))
    const names = rows.map((r) => r.split(',')[0] ?? '')
    const imp =
      rows.length === 3
        ? 'from matplotlib_venn import venn2 as venn_fn\nsubset = (vals[0], vals[1], vals[2])\nlabels = names[:2]'
        : 'from matplotlib_venn import venn3 as venn_fn\nsubset = (vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6])\nlabels = names[:3]'
    return `"""韦恩图（matplotlib_venn，区域元素数口径）。"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

vals = [${vals.join(', ')}]
names = ${JSON.stringify(names)}
${imp}

fig, ax = plt.subplots(figsize=(6, 6))
venn_fn(subsets=subset, set_labels=labels, ax=ax)
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
  (_v) => {
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
`
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
    const lines = data
      .trim()
      .split('\n')
      .filter((l) => l.trim())
    if (lines.length < 2) return INVALID
    return `"""系统树状图（scipy 层次聚类）。"""
import csv
import io
import json

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei", "Arial Unicode MS",
]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage

def parse_csv(text):
    rows = list(csv.reader(io.StringIO(text.strip())))
    return rows[0], rows[1:]

header, data_rows = parse_csv(${JSON.stringify(data)})
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
  subplotsSchema,
  wordcloudSchema,
  vennSchema,
  ganttSchema,
  dendrogramSchema,
  batchImageDownloadSchema
]
