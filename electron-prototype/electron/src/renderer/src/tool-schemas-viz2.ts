// tool-schemas-viz2.ts：W17 bulk_viz 图族交互页（画廊路由专用注册，不进工具箱卡片池）。
// 画廊卡片（topics_viz-<图族>-d<N> 变体）经 interactive-mapping 的图族表路由到本组页面
// （24 页归并 348 变体；注册进 interactiveGallerySchemas，仅 getToolSchema 可达）。
// 全部 matplotlib sidecar 运行 → PNG 进抽屉预览；内置数据模式（12 分布，种子 42，
// 与变体 d1~d12 同序，路由时按变体预选）。1d 图族用 gen_data(mode,n) 一列数值；
// matrix 图族固定内置场景（mode 字段仅保持表单一致）。
// 只依赖 interactive-tools 的类型（运行时零导入，注册方向是 interactive-tools → 本文件）。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

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

const P = (key: string, label: string, def: number, help?: string) => ({
  key, label, type: 'number' as const, default: def, width: 'half' as const, ...(help ? { help } : {})
})

const OUT = `fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

export interface VizType {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const vizFamily = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): VizType => ({ value, label, description, fields, body })


// ---------------------------------------------------------------------------
// 1D 图族 ×15
// ---------------------------------------------------------------------------
export const barVizSchema = vizFamily('bar', '柱状图',
  '分箱统计柱状图（内置模式自动分箱）。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
vals = [np.mean(data[i:i+10]) for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(labels, vals, color="tab:orange")`)

export const scatterVizSchema = vizFamily('scatter', '散点图',
  '索引-值散点（内置模式）。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(np.arange(len(data)), data, s=20, alpha=0.7)`)

export const stepVizSchema = vizFamily('step', '阶梯图',
  '阶梯折线（where=post）。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.step(np.arange(len(data)), data, where="post")`)

export const areaVizSchema = vizFamily('area', '面积图',
  '填充面积图。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.fill_between(np.arange(len(data)), data, alpha=0.4)
ax.plot(np.arange(len(data)), data)`)

export const errbarVizSchema = vizFamily('errbar', '误差条图',
  '分箱均值 ± 标准差误差条。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
means = [np.mean(data[i:i+10]) for i in range(0, len(data), 10)]
stds = [np.std(data[i:i+10]) for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(labels, means, yerr=stds, fmt="o", capsize=5)`)

export const stemVizSchema = vizFamily('stem', '火柴杆图',
  '离散信号火柴杆。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.stem(np.arange(len(data)), data)`)

export const dualaxisVizSchema = vizFamily('dualaxis', '双轴对比',
  '左轴原始值，右轴累积值。',
  [],
  () => `data = gen_data(mode, n)
fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(np.arange(len(data)), data, color="#3b82f6")
ax2 = ax1.twinx()
ax2.plot(np.arange(len(data)), np.cumsum(data), color="#ef4444", alpha=0.7)
ax2.set_ylabel("累积")`)

export const multiseriesVizSchema = vizFamily('multiseries', '多序列对比',
  '原始/滑动均值双线对比。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data, alpha=0.4, label="原始")
kernel = np.ones(5) / 5
ax.plot(np.arange(len(data)), np.convolve(data, kernel, mode="same"), label="滑动均值")
ax.legend()`)

export const polarRoseVizSchema = vizFamily('polar-rose', '极坐标玫瑰',
  '分箱角度统计玫瑰图。',
  [],
  () => `data = gen_data(mode, n)
hist, edges = np.histogram(data, bins=12)
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.bar(edges[:-1], hist, width=2 * np.pi / 12, alpha=0.7)`)

export const radarVizSchema = vizFamily('radar', '雷达图',
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

export const boxVizSchema = vizFamily('box', '箱线图',
  '分箱箱线图。',
  [],
  () => `data = gen_data(mode, n)
bins = [data[i:i+10] for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
ax.boxplot(bins, tick_labels=[f"第{i}组" for i in range(len(bins))])`)

export const violinVizSchema = vizFamily('violin', '小提琴图',
  '分箱小提琴分布。',
  [],
  () => `data = gen_data(mode, n)
bins = [data[i:i+10] for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(8, 5))
parts = ax.violinplot(bins, showmedians=True)
for pc in parts["bodies"]:
    pc.set_facecolor("tab:purple")
    pc.set_alpha(0.6)`)

export const hexbinVizSchema = vizFamily('hexbin', '六角分箱',
  '索引-值六角分箱密度。',
  [],
  () => `data = gen_data(mode, n)
x = np.arange(len(data))
y = data + rng.normal(0, 5, len(data))
fig, ax = plt.subplots(figsize=(8, 6))
hb = ax.hexbin(x, y, gridsize=25, cmap="viridis", mincnt=1)
fig.colorbar(hb, ax=ax)`)

export const hbarVizSchema = vizFamily('hbar', '水平条形图',
  '分箱水平条形（均值降序）。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
vals = [np.mean(data[i:i+10]) for i in range(0, len(data), 10)]
order = np.argsort(vals)
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh([labels[i] for i in order], [vals[i] for i in order], color="#10b981")`)

export const logVizSchema = vizFamily('log', '对数坐标',
  'Y 轴对数折线（取绝对值+1 防零）。',
  [],
  () => `data = np.abs(gen_data(mode, n)) + 1
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
ax.set_yscale("log")
ax.grid(True, alpha=0.3)`)

export const annotateVizSchema = vizFamily('annotate', '标注图',
  '峰值检测 + 箭头标注。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
peak = int(np.argmax(data))
ax.annotate(f"峰值 {data[peak]:.1f}", xy=(peak, data[peak]),
            xytext=(peak + 5, data[peak] + 10),
            arrowprops=dict(arrowstyle="->", color="red"))`)

export const insetVizSchema = vizFamily('inset', '局部放大',
  '主图 + 局部放大插图。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
mid = len(data) // 2
axins = ax.inset_axes([0.55, 0.5, 0.4, 0.45])
axins.plot(np.arange(mid - 10, mid + 10), data[mid - 10:mid + 10])
ax.indicate_inset_zoom(axins)`)

export const gridVizSchema = vizFamily('grid', '网格密底图',
  '密网格主次参考线。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data)
ax.grid(True, which="major", alpha=0.5)
ax.minorticks_on()
ax.grid(True, which="minor", alpha=0.15)`)

// ---------------------------------------------------------------------------
// 矩阵/特殊图族 ×6
// ---------------------------------------------------------------------------
export const heatmapVizSchema = vizFamily('heatmap', '热力图',
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

export const contourVizSchema = vizFamily('contour-filled', '等高线',
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

export const surfaceVizSchema = vizFamily('surface-3d', '三维曲面',
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

export const scatter3dVizSchema = vizFamily('scatter-3d', '三维散点',
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

export const wireframeVizSchema = vizFamily('wireframe-3d', '三维线框',
  '三维线框曲面（径向波）。',
  [],
  () => `x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X ** 2 + Y ** 2) * 2)
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
ax.plot_wireframe(X, Y, Z, rstride=2, cstride=2, color="#3b82f6", alpha=0.6)`)

export const bar3dVizSchema = vizFamily('bar-3d', '三维柱状',
  '三维柱状图（4×4 矩阵）。',
  [],
  () => `mat = rng.normal(50, 15, (4, 4))
x, y = np.meshgrid(range(4), range(4))
x, y = x.flatten(), y.flatten()
dz = mat.flatten()
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
ax.bar3d(x, y, np.zeros_like(x), 0.5, 0.5, dz, shade=True)`)

export const VIZ_TYPES: VizType[] = [
  vizFamily('grouped-bar', '分组柱状图',
  '多系列并列柱（覆盖 bulk_viz/dataviz grouped-bar）。',
  [P('groups', '组数', 4), P('series', '系列数', 3)],
  (v) => `groups = max(2, ${Math.max(2, Math.trunc(Number(v.groups) || 4))})
series = max(2, ${Math.max(2, Math.trunc(Number(v.series) || 3))})
vals = rng.uniform(20, 200, (series, groups))
x = np.arange(groups)
w = 0.8 / series
fig, ax = plt.subplots(figsize=(8, 5))
for i in range(series):
    ax.bar(x + (i - series / 2 + 0.5) * w, vals[i], w, label=f"系列{i + 1}", alpha=0.9)
ax.set_xticks(x, [f"组{i + 1}" for i in range(groups)])
ax.legend()`),
  vizFamily('stacked-bar', '堆叠柱状图',
  '多系列纵向堆叠（覆盖 dataviz stacked-bar）。',
  [P('groups', '组数', 4), P('series', '系列数', 3)],
  (v) => `groups = max(2, ${Math.max(2, Math.trunc(Number(v.groups) || 4))})
series = max(2, ${Math.max(2, Math.trunc(Number(v.series) || 3))})
vals = rng.uniform(10, 80, (series, groups))
x = np.arange(groups)
fig, ax = plt.subplots(figsize=(8, 5))
bottom = np.zeros(groups)
for i in range(series):
    ax.bar(x, vals[i], 0.6, bottom=bottom, label=f"系列{i + 1}", alpha=0.9)
    bottom += vals[i]
ax.set_xticks(x, [f"组{i + 1}" for i in range(groups)])
ax.legend()`),
  vizFamily('bubble', '气泡图',
  '三维变量散点：x/y/气泡大小 + 颜色（覆盖 dataviz bubble-chart）。',
  [P('n', '气泡数', 40)],
  (v) => `n = max(5, ${Math.max(5, Math.trunc(Number(v.n) || 40))})
x = rng.uniform(0, 100, n)
y = rng.uniform(0, 100, n)
size = rng.uniform(30, 600, n)
fig, ax = plt.subplots(figsize=(8, 5.5))
sc = ax.scatter(x, y, s=size, c=size, cmap="viridis", alpha=0.6, edgecolors="white")
fig.colorbar(sc, ax=ax, label="数值")
ax.grid(True, alpha=0.3)`),
  vizFamily('correlation', '相关系数矩阵',
  '多变量两两相关热力（覆盖 dataviz correlation-matrix）。',
  [P('vars', '变量数', 6), P('n', '样本数', 200)],
  (v) => `k = max(2, ${Math.max(2, Math.trunc(Number(v.vars) || 6))})
n = max(10, ${Math.max(10, Math.trunc(Number(v.n) || 200))})
base = rng.normal(0, 1, (k, n))
mix = (np.eye(k) + rng.uniform(-0.4, 0.9, (k, k)) * 0.5) @ base
corr = np.corrcoef(mix)
labels = [f"V{i + 1}" for i in range(k)]
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(k), labels)
ax.set_yticks(range(k), labels)
for i in range(k):
    for j in range(k):
        ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=8)
fig.colorbar(im, ax=ax, shrink=0.8)`),
  vizFamily('confidence-band', '置信带折线',
  '多试验均值线 ± 置信区间填充（覆盖 dataviz line-confidence-band）。',
  [P('n', '采样点', 400), P('trials', '试验次数', 20), P('level', '置信带宽', 1.96, 'z 倍标准差')],
  (v) => `n = max(20, ${Math.max(20, Math.trunc(Number(v.n) || 400))})
trials = max(3, ${Math.max(3, Math.trunc(Number(v.trials) || 20))})
z = ${Number(v.level) || 1.96}
runs = np.array([np.array(gen_data("sine" if i % 2 else "linear", n)) + rng.normal(0, 3, n) for i in range(trials)])
mean = runs.mean(axis=0)
std = runs.std(axis=0)
xs = np.arange(n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.fill_between(xs, mean - z * std, mean + z * std, alpha=0.25, label="置信区间")
ax.plot(xs, mean, color="#3b82f6", label="均值")
ax.legend()`),
  vizFamily('donut', '环形图',
  '占比环形（中心镂空，覆盖 dataviz/sciviz pie-donut）。',
  [P('slices', '扇区数', 5), P('width', '环宽', 0.4, '0~1')],
  (v) => `slices = max(2, ${Math.max(2, Math.trunc(Number(v.slices) || 5))})
width = min(0.95, max(0.05, ${Number(v.width) || 0.4}))
vals = rng.uniform(5, 40, slices)
labels = [f"类{i + 1}" for i in range(slices)]
fig, ax = plt.subplots(figsize=(7, 6))
ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90, counterclock=False,
       wedgeprops=dict(width=width, edgecolor="white"))
ax.text(0, 0, "占比", ha="center", va="center", fontsize=13)`),
  vizFamily('line', '折线图',
  '单序列折线（数据模式 ×12，覆盖 bulk_viz line 家族）。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(np.arange(len(data)), data, color="tab:blue", marker=".", markersize=4)`),
  vizFamily('pie', '饼图',
  '分箱占比饼图（覆盖 bulk_viz pie 家族）。',
  [],
  () => `data = gen_data(mode, n)
labels = [f"第{i}组" for i in range(0, len(data), 10)]
vals = [max(0.0, np.mean(data[i:i+10])) for i in range(0, len(data), 10)]
fig, ax = plt.subplots(figsize=(7, 6))
ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90, counterclock=False)`),
  vizFamily('hist', '直方图',
  '频率分布直方图（覆盖 bulk_viz hist 家族）。',
  [],
  () => `data = gen_data(mode, n)
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(data, bins=15, edgecolor="white", alpha=0.8, color="tab:purple")`),
  barVizSchema, scatterVizSchema, stepVizSchema, areaVizSchema,
  errbarVizSchema, stemVizSchema, dualaxisVizSchema, multiseriesVizSchema,
  polarRoseVizSchema, radarVizSchema, boxVizSchema, violinVizSchema,
  hexbinVizSchema, hbarVizSchema, logVizSchema, annotateVizSchema,
  insetVizSchema, gridVizSchema,
  heatmapVizSchema, contourVizSchema, surfaceVizSchema,
  scatter3dVizSchema, wireframeVizSchema, bar3dVizSchema
]

// ---------------------------------------------------------------------------
// 图表实验室：30 图族归并单页（类型选择器 + 动态参数表单）
// ---------------------------------------------------------------------------
export const VIZ_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '图表类型',
  type: 'select',
  default: 'bar',
  width: 'full',
  options: VIZ_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const vizLabSchema: InteractiveToolSchema = {
  id: 'interactive:viz-lab',
  title: '图表实验室',
  description: 'bulk_viz 30 图族 × 12 数据模式的归并页：选图表类型，调数据模式与参数，matplotlib 出图。',
  tags: ['图表'],
  fields: (v) => {
    const t = VIZ_TYPES.find((x) => x.value === v.type) ?? VIZ_TYPES[0]!
    return [VIZ_TYPE_FIELD, MODE_FIELD, POINTS_FIELD, ...t.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({
    rows: [
      { label: '图表类型', value: String(v.type ?? 'bar') },
      { label: '数据模式', value: String(v.mode ?? 'sine') },
      { label: '点数', value: String(v.points ?? 60) }
    ]
  }),
  pyCode: (v) => {
    const t = VIZ_TYPES.find((x) => x.value === v.type) ?? VIZ_TYPES[0]!
    const mode = str(v.mode ?? 'sine')
    const n = Math.max(5, Math.trunc(Number(v.points ?? 60)) || 60)
    const decl = `mode = ${JSON.stringify(mode)}\nn = ${n}\n`
    return `import json\n${GEN_HEAD}\n${decl}\n${t.body({ ...v, mode, n })}\n\n${OUT}`
  }
}
