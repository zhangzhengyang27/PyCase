// tool-schemas-sciviz.ts：科研出版级绘图实验室（sciviz 命名单例 15 家族归并单页）。
// 全部用纯 matplotlib + 合成数据重实现（原示例绑 python-ternary/netCDF4/seaborn 课件数据，
// 实验室语义等价、参数可调、零额外依赖）。画廊路由专用注册。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const SV_HEAD = `import json
import math

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei", "Arial Unicode MS",
]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath
import numpy as np

rng = np.random.default_rng(7)
`

const SV_OUT = `fig.tight_layout()
fig.savefig("chart.png", dpi=150)
print("已输出 chart.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "chart.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

export interface SciVizType {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const P = (key: string, label: string, def: number, help?: string) => ({
  key, label, type: 'number' as const, default: def, width: 'half' as const, ...(help ? { help } : {})
})

const svFamily = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): SciVizType => ({ value, label, description, fields, body })

export const SCIVIZ_TYPES: SciVizType[] = [
  svFamily('ternary', '三元相图',
  '三组分归一化散点（纯 matplotlib 重实现，等价 python-ternary）。',
  [P('n', '样本数', 220)],
  (v) => `n = max(20, ${Math.max(20, Math.trunc(Number(v.n) || 220))})
raw = rng.dirichlet([2, 3, 4], n)
corners = np.array([[0, 0], [1, 0], [0.5, math.sqrt(3) / 2]])
pts = raw @ corners
fig, ax = plt.subplots(figsize=(7, 6.5))
tri = mpatches.Polygon(corners, closed=True, fill=False, edgecolor="k", linewidth=1.6)
ax.add_patch(tri)
for s in range(1, 5):
    t = s / 5
    for a, b in [((0, 0), (1, 0)), ((1, 0), (0.5, math.sqrt(3) / 2)), ((0.5, math.sqrt(3) / 2), (0, 0))]:
        p = a + (b - a) * t
        ax.plot([p[0], 0.5], [p[1], 0.5 * math.sqrt(3) / 2 + (p[1] * 0)], color="0.85", lw=0.6, zorder=0)
ax.scatter(pts[:, 0], pts[:, 1], s=16, c=raw[:, 2], cmap="viridis", alpha=0.85)
ax.set_xlim(-0.08, 1.08)
ax.set_ylim(-0.08, 0.95)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("A（左下）· B（右下）· C（顶）")`),
  svFamily('streamplot', '流线场',
  '二维速度场流线（streamplot，双涡旋合成场）。',
  [P('density', '流线密度', 1.4)],
  (v) => `density = max(0.5, ${Number(v.density) || 1.4})
y, x = np.mgrid[-3:3:120j, -3:3:160j]
u = np.sin(x) * np.cos(y) - y / 3
vv = -np.cos(x) * np.sin(y) + x / 3
speed = np.sqrt(u ** 2 + vv ** 2)
fig, ax = plt.subplots(figsize=(8, 5.5))
strm = ax.streamplot(x, y, u, vv, color=speed, cmap="coolwarm", density=density, linewidth=1.1)
fig.colorbar(strm.lines, ax=ax, label="流速")
ax.set_title("合成速度场")`),
  svFamily('pcolor', '伪彩场',
  '网格标量场 pcolor 着色（覆盖 sciviz pcolor-fields）。',
  [P('n', '网格密度', 60)],
  (v) => `n = max(10, ${Math.max(10, Math.trunc(Number(v.n) || 60))})
y, x = np.mgrid[-3:3:complex(n), -4:4:complex(n * 4 // 3)]
z = np.exp(-((x - 1) ** 2 + (y + 0.5) ** 2)) + 0.6 * np.exp(-((x + 1.5) ** 2 + (y - 1) ** 2) / 2)
fig, ax = plt.subplots(figsize=(8, 5))
pc = ax.pcolormesh(x, y, z, cmap="magma", shading="auto")
fig.colorbar(pc, ax=ax)
ax.set_title("二维标量场")`),
  svFamily('unstructured-mesh', '非结构网格',
  '散点三角剖分连续场（tricontourf，覆盖 sciviz unstructured-mesh）。',
  [P('n', '散点数', 350)],
  (v) => `n = max(60, ${Math.max(60, Math.trunc(Number(v.n) || 350))})
x = rng.uniform(-4, 4, n)
y = rng.uniform(-3, 3, n)
z = np.sin(2 * x) * np.cos(1.5 * y) + 0.3 * rng.normal(0, 1, n)
fig, ax = plt.subplots(figsize=(8, 5.5))
tm = ax.tricontourf(x, y, z, levels=18, cmap="viridis")
ax.tricontour(x, y, z, levels=18, colors="k", linewidths=0.3, alpha=0.4)
ax.plot(x, y, "k.", markersize=1.5, alpha=0.4)
fig.colorbar(tm, ax=ax)
ax.set_title("非结构散点三角剖分")`),
  svFamily('slope', '斜率图',
  '两时点变化对比 slope graph（覆盖 sciviz slope-graph）。',
  [P('items', '条目数', 8)],
  (v) => `items = max(3, ${Math.max(3, Math.trunc(Number(v.items) || 8))})
before = rng.uniform(20, 100, items)
after = before + rng.normal(6, 12, items)
fig, ax = plt.subplots(figsize=(7, 6))
for i in range(items):
    up = after[i] >= before[i]
    ax.plot([0, 1], [before[i], after[i]], color="#2a9d8f" if up else "#e76f51", lw=1.6, alpha=0.85, marker="o", markersize=4)
    ax.text(-0.04, before[i], f"项{i + 1}  {before[i]:.0f}", ha="right", va="center", fontsize=8)
    ax.text(1.04, after[i], f"{after[i]:.0f}", ha="left", va="center", fontsize=8)
ax.set_xticks([0, 1], ["之前", "之后"])
ax.set_xlim(-0.5, 1.5)
for sp in ("top", "right", "bottom"):
    ax.spines[sp].set_visible(False)
ax.set_title("绿升红降")`),
  svFamily('line-styles', '线型样式板',
  '线型/标记/虚线周期一览（覆盖 sciviz line-styles）。',
  [],
  () => `styles = [("-", "实线"), ("--", "虚线"), ("-.", "点划线"), (":", "点线"),
          ("o", "圆标记"), ("s", "方标记"), ("^", "三角标记")]
x = np.linspace(0, 10, 60)
fig, ax = plt.subplots(figsize=(8, 5))
for i, (st, name) in enumerate(styles):
    ys = 8 - i + np.sin(x + i) * 0.7
    ax.plot(x, ys, st, label=name, lw=1.8, markersize=5, markevery=8)
ax.legend(ncol=2, fontsize=8)
ax.set_ylim(0, 10)`),
  svFamily('canvas-axes', '画布与坐标轴解剖',
  'Figure/Axes/轴脊/刻度标注图（覆盖 sciviz canvas-axes）。',
  [],
  () => `fig, ax = plt.subplots(figsize=(8, 5.5))
ax.annotate("Figure 画布", xy=(0.02, 0.97), xycoords="figure fraction", fontsize=11, color="#666")
ax.annotate("Axes 绘图区", xy=(0.5, 0.5), xycoords="axes fraction", ha="center", fontsize=13)
ax.annotate("x 轴刻度", xy=(0.5, -0.12), xycoords="axes fraction", ha="center", fontsize=9, color="#2a9d8f")
ax.annotate("y 轴刻度", xy=(-0.16, 0.5), xycoords="axes fraction", fontsize=9, color="#2a9d8f", rotation=90)
ax.annotate("标题", xy=(0.5, 1.04), xycoords="axes fraction", ha="center", fontsize=10)
ax.annotate("上脊线", xy=(0.5, 1.0), xycoords="axes fraction", ha="center", fontsize=8, color="#e76f51")
ax.set_xticks(np.linspace(0, 1, 6))
ax.set_yticks(np.linspace(0, 1, 5))
ax.grid(True, alpha=0.25)`),
  svFamily('complex-axes', '复合坐标系',
  '内嵌插图 + 双轴 + 次刻度（覆盖 sciviz complex-axes）。',
  [],
  () => `x = np.linspace(0, 10, 300)
main = np.sin(x) * np.exp(-x / 8)
fig, ax = plt.subplots(figsize=(8.5, 5.5))
ax.plot(x, main, label="主线", color="#3b82f6")
ax2 = ax.twinx()
ax2.plot(x, np.cumsum(np.abs(main)), color="#ef4444", alpha=0.7, label="累计（右轴）")
axins = ax.inset_axes([0.58, 0.55, 0.36, 0.34])
axins.plot(x[40:90], main[40:90], color="#3b82f6")
axins.tick_params(labelsize=7)
ax.indicate_inset_zoom(axins, edgecolor="#888")
ax.set_title("主图 + 右轴 + 局部放大")
ax.legend(loc="lower left", fontsize=8)`),
  svFamily('data-formats', '数据格式输入',
  'list / ndarray / 字典三种数据源画同一张图（覆盖 sciviz data-formats）。',
  [],
  () => `xs_list = [0, 1, 2, 3, 4]
xs_np = np.linspace(0, 4, 40)
xs_dict = {"x": xs_list, "y": [1.2, 2.8, 2.1, 4.4, 3.9]}
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(xs_np, np.interp(xs_np, xs_list, xs_dict["y"]), "--", color="0.8", label="ndarray 插值")
ax.plot(xs_dict["x"], xs_dict["y"], "o-", label="dict")
ax.plot(xs_list, [v * 0.9 for v in xs_dict["y"]], "s--", ms=5, label="list")
ax.legend(fontsize=8)
ax.set_title("三种数据源同图")`),
  svFamily('pandas-plot', 'DataFrame 绘图',
  'pandas df.plot 高层接口（列自动成系列）。',
  [],
  () => `import pandas as pd
idx = pd.period_range("2024Q1", periods=6, freq="Q")
df = pd.DataFrame({"营收": [120, 135, 148, 160, 172, 190],
                   "成本": [90, 96, 108, 118, 125, 138]}, index=idx.astype(str))
fig, ax = plt.subplots(figsize=(8, 5))
df.plot.bar(ax=ax, alpha=0.9)
ax.set_title("df.plot.bar()：列即系列")
ax.legend(fontsize=8)`),
  svFamily('3d-profile', '三维剖面',
  '曲面 + 底面等高线投影（覆盖 sciviz 3d-profile）。',
  [P('levels', '等高线级数', 12)],
  (v) => `levels = max(4, ${Math.max(4, Math.trunc(Number(v.levels) || 12))})
x = np.linspace(-3, 3, 70)
y = np.linspace(-3, 3, 70)
X, Y = np.meshgrid(x, y)
Z = np.exp(-((X - 0.8) ** 2 + (Y + 0.4) ** 2)) + 0.55 * np.exp(-((X + 1.2) ** 2 + (Y - 1) ** 2) / 1.6)
fig = plt.figure(figsize=(9, 6.5))
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.85, linewidth=0, antialiased=True)
ax.contourf(X, Y, Z, levels=levels, zdir="z", offset=-0.35, cmap="viridis", alpha=0.7)
ax.set_zlim(-0.35, 1.3)
fig.colorbar(surf, ax=ax, shrink=0.55)
ax.set_title("曲面 + 底面等高线投影")`),
  svFamily('3d-bars', '三维柱状',
  '分面三维柱状阵列（覆盖 sciviz 3d-bars）。',
  [P('rows', '行数', 5), P('cols', '列数', 6)],
  (v) => `rows = max(2, ${Math.max(2, Math.trunc(Number(v.rows) || 5))})
cols = max(2, ${Math.max(2, Math.trunc(Number(v.cols) || 6))})
heights = rng.uniform(0.2, 1, (rows, cols))
xs, ys = np.meshgrid(np.arange(cols), np.arange(rows))
xs, ys, dz = xs.flatten(), ys.flatten(), heights.flatten()
fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection="3d")
colors = plt.cm.plasma(dz / dz.max())
ax.bar3d(xs, ys, np.zeros_like(xs), 0.6, 0.6, dz, color=colors, shade=True)
ax.set_title("矩阵高度三维柱")
ax.view_init(elev=28, azim=-50)`),
  svFamily('stats-style', '出版级统计图',
  '箱线 + 小提琴 + 抖动散点三联（等价 seaborn 风格，纯 matplotlib）。',
  [P('groups', '组数', 4), P('n', '每组样本', 60)],
  (v) => `groups = max(2, ${Math.max(2, Math.trunc(Number(v.groups) || 4))})
n = max(20, ${Math.max(20, Math.trunc(Number(v.n) || 60))})
data = [rng.normal(50 + i * 7, 9 + i, n) for i in range(groups)]
positions = np.arange(1, groups + 1)
fig, ax = plt.subplots(figsize=(8.5, 5.5))
vp = ax.violinplot(data, positions=positions, widths=0.85, showextrema=False)
for body in vp["bodies"]:
    body.set_facecolor("#8ecae6")
    body.set_alpha(0.55)
bp = ax.boxplot(data, positions=positions, widths=0.16, patch_artist=True)
for box in bp["boxes"]:
    box.set_facecolor("#023047")
for i, d in enumerate(data):
    ax.plot(positions[i] + rng.uniform(-0.09, 0.09, len(d)), d, ".", color="#fb8500", ms=3, alpha=0.6)
ax.set_xticks(positions, [f"组{i + 1}" for i in range(groups)])
ax.set_title("violin + box + strip（出版风格）")`),
  svFamily('box-violin', '箱线小提琴对',
  '同一数据的箱线/小提琴并排对照（覆盖 sciviz box-violin）。',
  [P('n', '每组样本', 80)],
  (v) => `n = max(20, ${Math.max(20, Math.trunc(Number(v.n) || 80))})
data = [rng.normal(40 + i * 9, 7 + i * 1.5, n) for i in range(3)]
pos = [1, 1.9, 2.8]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
ax1.boxplot(data, positions=pos, widths=0.5, patch_artist=True,
            boxprops=dict(facecolor="#bdb2ff"))
ax1.set_title("箱线图")
ax2.violinplot(data, positions=pos, widths=0.75, showmedians=True)
ax2.set_title("小提琴图")
for ax in (ax1, ax2):
    ax.set_xticks(pos, [f"组{i + 1}" for i in range(3)])`),
  svFamily('chord', '弦图',
  '节点关系弦图（圆弧 + 贝塞尔带，纯 matplotlib 重实现）。',
  [P('nodes', '节点数', 6), P('links', '关系数', 9)],
  (v) => `nodes = max(3, ${Math.max(3, Math.trunc(Number(v.nodes) || 6))})
links = max(nodes, ${Math.max(3, Math.trunc(Number(v.links) || 9))})
pairs = [tuple(rng.choice(nodes, 2, replace=False)) for _ in range(links)]
weights = rng.uniform(0.2, 1, links)
colors = plt.cm.tab10(np.arange(nodes) % 10)
def arc(cx, cy, r, a0, a1):
    ts = np.linspace(a0, a1, 60)
    return cx + r * np.cos(ts), cy + r * np.sin(ts)
fig, ax = plt.subplots(figsize=(7.5, 7))
R = 1.0
gap = 2 * math.pi / nodes * 0.18
seg = 2 * math.pi / nodes - gap
for i in range(nodes):
    a0 = i * 2 * math.pi / nodes + gap / 2
    xs, ys = arc(0, 0, R, a0, a0 + seg)
    ax.plot(xs, ys, color=colors[i], lw=5, solid_capstyle="butt")
    mid = a0 + seg / 2
    ax.text(1.14 * R * math.cos(mid), 1.14 * R * math.sin(mid), f"N{i}", ha="center", va="center", fontsize=9)
for k, (a, b) in enumerate(pairs):
    if a == b:
        continue
    aa = (a + 0.5) * 2 * math.pi / nodes
    ab = (b + 0.5) * 2 * math.pi / nodes
    p0, p3 = (R * math.cos(aa), R * math.sin(aa)), (R * math.cos(ab), R * math.sin(ab))
    ctrl = (0, 0)
    path = MplPath([p0, ctrl, p3], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
    ax.add_patch(mpatches.PathPatch(path, facecolor=colors[a], alpha=0.25 + 0.4 * weights[k], edgecolor="none", lw=0))
ax.set_xlim(-1.35, 1.35)
ax.set_ylim(-1.35, 1.35)
ax.set_aspect("equal")
ax.axis("off")`)
]

// ---------------------------------------------------------------------------
// 科研绘图实验室：15 家族归并单页（类型选择器 + 动态参数表单）
// ---------------------------------------------------------------------------
const SCIVIZ_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '图形',
  type: 'select',
  default: 'streamplot',
  width: 'full',
  options: SCIVIZ_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const scivizLabSchema: InteractiveToolSchema = {
  id: 'interactive:sciviz-lab',
  title: '科研绘图实验室',
  description: 'sciviz 出版级图形归并页：三元相图 / 流线场 / 非结构网格 / 弦图 / 出版级统计图等，纯 matplotlib + 合成数据。',
  tags: ['科研', '图表'],
  fields: (v) => {
    const t = SCIVIZ_TYPES.find((x) => x.value === v.type) ?? SCIVIZ_TYPES[0]!
    return [SCIVIZ_TYPE_FIELD, ...t.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '图形', value: String(v.type ?? 'streamplot') }] }),
  pyCode: (v) => {
    const t = SCIVIZ_TYPES.find((x) => x.value === v.type) ?? SCIVIZ_TYPES[0]!
    return `${SV_HEAD}\n${t.body(v)}\n${SV_OUT}`
  }
}
