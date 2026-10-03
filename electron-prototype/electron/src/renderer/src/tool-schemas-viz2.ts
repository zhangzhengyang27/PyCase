// tool-schemas-viz2.ts：W17 bulk_viz 剩余 21 图族交互页（252 变体归并）。
// 全部 matplotlib sidecar 运行 → PNG 进抽屉预览；内置数据模式（12 分布，种子 42）。
// 1d 图族用 gen_data(mode,n) 一列数值；matrix 图族固定内置场景。
// 只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')

const GEN_HEAD = `import math
import random

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei", "Arial Unicode MS",
]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np

random.seed(42)
rng = np.random.default_rng(7)

def gen_data(mode, n):
    gens = {
        "sine": lambda i: math.sin(i / 5) + random.uniform(-0.3, 0.3),
        "linear": lambda i: i * 0.8 + 2,
        "exp": lambda i: 100 * math.exp(-i / 15),
        "random": lambda i: random.uniform(0, 100),
        "normal": lambda i: random.gauss(50, 12),
        "pulse": lambda i: 100 if (i // 10) % 2 == 0 else 20,
        "step": lambda i: 50 * (i // 8),
        "bimodal": lambda i: random.gauss(30, 8) if i % 2 else random.gauss(70, 8),
        "sawtooth": lambda i: (i % 12) * 8,
        "spike": lambda i: min(100, i * 2) if i < n - 5 else 100 - (i - n + 5) * 20,
        "sparse": lambda i: random.uniform(10, 30) + (80 if i % 15 == 0 else 0),
        "square": lambda i: i ** 2 / 10,
    }
    fn = gens.get(mode, gens["sine"])
    return [fn(i) for i in range(n)]
`

const MODE_FIELD = {
  key: 'mode',
  label: '数据模式',
  type: 'select' as const,
  default: 'sine',
  width: 'half' as const,
  options: [
    { value: 'sine', label: '正弦加噪' },
    { value: 'linear', label: '线性趋势' },
    { value: 'exp', label: '指数衰减' },
    { value: 'random', label: '均匀随机' },
    { value: 'normal', label: '聚簇正态' },
    { value: 'pulse', label: '周期脉冲' },
    { value: 'step', label: '阶梯平台' },
    { value: 'bimodal', label: '双峰分布' },
    { value: 'sawtooth', label: '锯齿波' },
    { value: 'spike', label: '缓升陡降' },
    { value: 'sparse', label: '稀疏脉冲' },
    { value: 'square', label: '平方增长' }
  ]
}

const POINTS_FIELD = { key: 'points', label: '点数', type: 'number' as const, default: 60, width: 'half' as const }

const OUT = `fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

function vizBase(
  id: string,
  title: string,
  description: string,
  extraFields: InteractiveToolSchema['fields'],
  body: (v: Record<string, unknown>) => string,
  needsJson = false
): InteractiveToolSchema {
  return {
    id: `interactive:viz-${id}`,
    title,
    description,
    tags: ['图表'],
    fields: [MODE_FIELD, POINTS_FIELD, ...extraFields],
    computeVia: 'sidecar',
    compute: (v) => {
      const mode = str(v.mode ?? 'sine')
      const n = Math.max(5, Math.trunc(Number(v.points ?? 60)) || 60)
      return { rows: [{ label: '数据模式', value: mode }, { label: '点数', value: String(n) }] }
    },
    pyCode: (v) => {
      const mode = str(v.mode ?? 'sine')
      const n = Math.max(5, Math.trunc(Number(v.points ?? 60)) || 60)
      const jsonImport = 'import json\n'
      const decl = `mode = ${JSON.stringify(mode)}\nn = ${n}\n`
      return `${jsonImport}${GEN_HEAD}
${decl}
${body({ mode, n })}

${OUT}`
    }
  }
}

// ---------------------------------------------------------------------------
// 1D 图族 ×15
// ---------------------------------------------------------------------------
export const barVizSchema = vizBase('bar', '柱状图',
  '分箱统计柱状图（内置模式自动分箱）。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
vals = [np.mean(data[i:i+10]) for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(labels, vals, color="tab:orange")`)

export const scatterVizSchema = vizBase('scatter', '散点图',
  '索引-值散点（内置模式）。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(np.arange(len(data)), data, s=20, alpha=0.7)`)

export const stepVizSchema = vizBase('step', '阶梯图',
  '阶梯折线（where=post）。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.step(np.arange(len(data)), data, where="post")`)

export const areaVizSchema = vizBase('area', '面积图',
  '填充面积图。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.fill_between(np.arange(len(data)), data, alpha=0.4)
ax.plot(np.arange(len(data)), data)`)

export const errbarVizSchema = vizBase('errbar', '误差条图',
  '分箱均值 ± 标准差误差条。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
means = [np.mean(data[i:i+10]) for i in range(0, len(data), 10)]
stds = [np.std(data[i:i+10]) for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(labels, means, yerr=stds, fmt="o", capsize=5)`)

export const stemVizSchema = vizBase('stem', '火柴杆图',
  '离散信号火柴杆。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.stem(np.arange(len(data)), data)`)

export const dualaxisVizSchema = vizBase('dualaxis', '双轴对比',
  '左轴原始值，右轴累积值。',
  [],
  () => `data = gen_data(mode, n)
fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(np.arange(len(data)), data, color="#3b82f6")
ax2 = ax1.twinx()
ax2.plot(np.arange(len(data)), np.cumsum(data), color="#ef4444", alpha=0.7)
ax2.set_ylabel("累积")`)

export const multiseriesVizSchema = vizBase('multiseries', '多序列对比',
  '原始/滑动均值双线对比。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data, alpha=0.4, label="原始")
kernel = np.ones(5) / 5
ax.plot(np.arange(len(data)), np.convolve(data, kernel, mode="same"), label="滑动均值")
ax.legend()`)

export const polarRoseVizSchema = vizBase('polar-rose', '极坐标玫瑰',
  '分箱角度统计玫瑰图。',
  [],
  () => `data = gen_data(mode, n)
hist, edges = np.histogram(data, bins=12)
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.bar(edges[:-1], hist, width=2 * np.pi / 12, alpha=0.7)`)

export const radarVizSchema = vizBase('radar', '雷达图',
  '五分位数统计雷达（P10~P90）。',
  [],
  () => `data = gen_data(mode, n)
quants = [np.percentile(data, q) for q in (10, 30, 50, 70, 90)]
labels = ["P10", "P30", "P50", "P70", "P90"]
angles = np.linspace(0, 2 * np.pi, 5, endpoint=False).tolist()
vals = quants + quants[:1]
angles += angles[:1]
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, vals)
ax.fill(angles, vals, alpha=0.2)
ax.set_xticks(angles[:-1], labels)`)

export const boxVizSchema = vizBase('box', '箱线图',
  '分箱箱线图。',
  [],
  () => `data = gen_data(mode, n)
bins = [data[i:i+10] for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
ax.boxplot(bins, tick_labels=[f"第{i}组" for i in range(len(bins))])`)

export const violinVizSchema = vizBase('violin', '小提琴图',
  '分箱小提琴分布。',
  [],
  () => `data = gen_data(mode, n)
bins = [data[i:i+10] for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
parts = ax.violinplot(bins, showmedians=True)
for pc in parts["bodies"]:
    pc.set_facecolor("tab:purple")
    pc.set_alpha(0.6)`)

export const hexbinVizSchema = vizBase('hexbin', '六角分箱',
  '索引-值六角分箱密度。',
  [],
  () => `data = gen_data(mode, n)
x = np.arange(len(data))
y = data + rng.normal(0, 5, len(data))
fig, ax = plt.subplots(figsize=(8, 6))
hb = ax.hexbin(x, y, gridsize=25, cmap="viridis", mincnt=1)
fig.colorbar(hb, ax=ax)`)

export const hbarVizSchema = vizBase('hbar', '水平条形图',
  '分箱水平条形（均值降序）。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
vals = [np.mean(data[i:i+10]) for i in range(0, len(data), 10)]
order = np.argsort(vals)
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh([labels[i] for i in order], [vals[i] for i in order], color="#10b981")`)

export const logVizSchema = vizBase('log', '对数坐标',
  'Y 轴对数折线（取绝对值+1 防零）。',
  [],
  () => `data = np.abs(gen_data(mode, n)) + 1
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
ax.set_yscale("log")
ax.grid(True, alpha=0.3)`)

export const annotateVizSchema = vizBase('annotate', '标注图',
  '峰值检测 + 箭头标注。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
peak = int(np.argmax(data))
ax.annotate(f"峰值 {data[peak]:.1f}", xy=(peak, data[peak]),
            xytext=(peak + 5, data[peak] + 10),
            arrowprops=dict(arrowstyle="->", color="red"))`)

export const insetVizSchema = vizBase('inset', '局部放大',
  '主图 + 局部放大插图。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
mid = len(data) // 2
axins = ax.inset_axes([0.55, 0.5, 0.4, 0.45])
axins.plot(np.arange(mid - 10, mid + 10), data[mid - 10:mid + 10])
ax.indicate_inset_zoom(axins)`)

export const gridVizSchema = vizBase('grid', '网格密底图',
  '密网格主次参考线。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
ax.grid(True, which="major", alpha=0.5)
ax.minorticks_on()
ax.grid(True, which="minor", alpha=0.15)`)

export const subplotsVizSchema = vizBase('subplots', '双子图布局',
  '上下双子图（原始/滑动均值）。',
  [],
  () => `data = gen_data(mode, n)
kernel = np.ones(7) / 7
smooth = np.convolve(data, kernel, mode="same")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
ax1.plot(np.arange(len(data)), data)
ax1.set_title("原始")
ax2.plot(np.arange(len(smooth)), smooth, color="tab:orange")
ax2.set_title("平滑")`)

// ---------------------------------------------------------------------------
// 矩阵/特殊图族 ×6
// ---------------------------------------------------------------------------
export const heatmapVizSchema = vizBase('heatmap', '热力图',
  '随机矩阵热力（行列可调）。',
  [
    { key: 'rows', label: '行数', type: 'number', default: 10, width: 'half' },
    { key: 'cols', label: '列数', type: 'number', default: 8, width: 'half' }
  ],
  (v) => {
    const r = Math.max(2, Math.trunc(Number(v.rows ?? 10)) || 10)
    const c = Math.max(2, Math.trunc(Number(v.cols ?? 8)) || 8)
    return `mat = rng.normal(50, 15, (${r}, ${c}))
fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(mat, cmap="YlOrRd", aspect="auto")
fig.colorbar(im, ax=ax)`
  })

export const contourVizSchema = vizBase('contour-filled', '等高线',
  '二维高斯场等高线（filled，levels 可调）。',
  [{ key: 'levels', label: '级数', type: 'number', default: 15, width: 'half' }],
  (v) => {
    const levels = Math.max(3, Math.trunc(Number(v.levels ?? 15)) || 15)
    return `x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)
Z = np.exp(-(X ** 2 + Y ** 2) / 2)
fig, ax = plt.subplots(figsize=(8, 6))
cs = ax.contourf(X, Y, Z, levels=${levels}, cmap="coolwarm")
fig.colorbar(cs, ax=ax)`
  })

export const surfaceVizSchema = vizBase('surface-3d', '三维曲面',
  '三维双峰高斯曲面。',
  [],
  () => `x = np.linspace(-3, 3, 60)
y = np.linspace(-3, 3, 60)
X, Y = np.meshgrid(x, y)
Z = np.exp(-((X - 1) ** 2 + (Y + 0.5) ** 2)) + 0.5 * np.exp(-((X + 1.5) ** 2 + (Y - 1) ** 2) / 2)
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X, Y, Z, cmap="viridis", edgecolor="k", linewidth=0.1)
fig.colorbar(surf, ax=ax, shrink=0.6)`)

export const scatter3dVizSchema = vizBase('scatter-3d', '三维散点',
  '三簇高斯三维散点。',
  [],
  () => `pts = np.vstack([
    rng.normal([2, 2, 2], 0.5, (20, 3)),
    rng.normal([-2, 0, 1], 0.5, (20, 3)),
    rng.normal([0, -2, -1], 0.5, (20, 3)),
])
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=pts[:, 2], cmap="coolwarm")`)

export const wireframeVizSchema = vizBase('wireframe-3d', '三维线框',
  '三维线框曲面（径向波）。',
  [],
  () => `x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X ** 2 + Y ** 2) * 2)
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
ax.plot_wireframe(X, Y, Z, rstride=2, cstride=2, color="#3b82f6", alpha=0.6)`)

export const bar3dVizSchema = vizBase('bar-3d', '三维柱状',
  '三维柱状图（4×4 矩阵）。',
  [],
  () => `mat = rng.normal(50, 15, (4, 4))
x, y = np.meshgrid(range(4), range(4))
x, y = x.flatten(), y.flatten()
dz = mat.flatten()
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
ax.bar3d(x, y, np.zeros_like(x), 0.5, 0.5, dz, shade=True)`)

export const VIZ2_SCHEMAS: InteractiveToolSchema[] = [
  barVizSchema, scatterVizSchema, stepVizSchema, areaVizSchema,
  errbarVizSchema, stemVizSchema, dualaxisVizSchema, multiseriesVizSchema,
  polarRoseVizSchema, radarVizSchema, boxVizSchema, violinVizSchema,
  hexbinVizSchema, hbarVizSchema, logVizSchema, annotateVizSchema,
  insetVizSchema, gridVizSchema, subplotsVizSchema,
  heatmapVizSchema, contourVizSchema, surfaceVizSchema,
  scatter3dVizSchema, wireframeVizSchema, bar3dVizSchema
]
