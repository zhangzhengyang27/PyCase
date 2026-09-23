// facets.ts：筛选条芯片组（运行状态 × 主题 × 质量分 × 标签）
// 画廊与工具箱各一个挂载点；所有维度变化统一走 applyAllFilters。
// 纯过滤逻辑在 filter-engine.ts；本模块只负责芯片渲染与交互。
// 计数口径：各维度芯片统计时剥离 theme/quality/tags 自身维度（只叠加收藏+运行状态+搜索），
// 与 buildTagFacets 的「除本维度外」口径一致。

import { state, els, THEMES } from './state'
import * as FilterEngine from './filter-engine'
import { escapeHtml } from './utils'
import { applyAllFilters, currentFilterQuery, filterContext, persistViewPrefs } from './app'

const RUN_STATUS_FACETS = [
  { key: 'all', label: '全部' },
  { key: 'ok', label: '成功过' },
  { key: 'failed', label: '失败过' },
  { key: 'never', label: '未运行' }
]
const TAG_FACET_LIMIT = 15
const QUALITY_FACETS = [
  { min: 0, label: '全部' },
  { min: 90, label: '90+' },
  { min: 80, label: '80+' },
  { min: 60, label: '60+' }
]

const CHIP_CLS =
  'facet-chip border border-line-subtle bg-transparent text-ink-dim rounded-full px-[9px] py-0.5 text-[11px] font-sans cursor-pointer transition-all duration-[120ms] hover:text-ink'
const GROUP_LABEL_CLS = 'facet-label shrink-0 text-[10.5px] text-ink-mute leading-5 w-[30px]'
const GROUP_CLS = 'facet-group flex items-start gap-2'

/** 计数基准：剥离 theme/quality/tags 维度后的查询 */
function baseQuery(overrides?: any) {
  return { ...currentFilterQuery(overrides), tags: [], theme: 'all', minQuality: 0 }
}

interface FacetCounts {
  themeCounts: Map<string, number>
  qualityCounts: Map<number, number>
}

function computeCounts(list): FacetCounts {
  const ctx = filterContext()
  const themeCounts = new Map<string, number>()
  const qualityCounts = new Map<number, number>()
  const base = baseQuery()
  const list0 = list || []
  for (const ex of list0) {
    if (!FilterEngine.matchExample(ex, base, ctx)) continue
    for (const t of THEMES) {
      if (t.filter(ex)) themeCounts.set(t.key, (themeCounts.get(t.key) || 0) + 1)
    }
    for (const qf of QUALITY_FACETS) {
      if (qf.min === 0) continue
      if ((ex.quality_score ?? 0) >= qf.min) qualityCounts.set(qf.min, (qualityCounts.get(qf.min) || 0) + 1)
    }
  }
  return { themeCounts, qualityCounts }
}

function statusGroupHtml(): string {
  const btns = RUN_STATUS_FACETS.map(
    (s) =>
      `<button class="${CHIP_CLS}${state.activeRunStatus === s.key ? ' active' : ''}" data-kind="status" data-value="${s.key}">${s.label}</button>`
  ).join('')
  return `<div class="${GROUP_CLS}"><span class="${GROUP_LABEL_CLS}">运行</span><div class="flex flex-wrap gap-1 flex-1">${btns}</div></div>`
}

function themeGroupHtml(counts: FacetCounts): string {
  const allBtn = `<button class="${CHIP_CLS}${state.activeTheme === 'all' ? ' active' : ''}" data-kind="theme" data-value="all">全部主题</button>`
  const btns = THEMES.map((t) => {
    const n = counts.themeCounts.get(t.key) || 0
    return `<button class="${CHIP_CLS}${state.activeTheme === t.key ? ' active' : ''}" data-kind="theme" data-value="${t.key}" title="${t.placeholder}">${t.icon} ${t.label} ${n}</button>`
  }).join('')
  return `<div class="${GROUP_CLS}"><span class="${GROUP_LABEL_CLS}">主题</span><div class="flex flex-wrap gap-1 flex-1">${allBtn}${btns}</div></div>`
}

function qualityGroupHtml(counts: FacetCounts): string {
  const btns = QUALITY_FACETS.map((qf) => {
    const n = qf.min === 0 ? '' : ` ${counts.qualityCounts.get(qf.min) || 0}`
    return `<button class="${CHIP_CLS}${state.minQuality === qf.min ? ' active' : ''}" data-kind="quality" data-value="${qf.min}">${qf.label}${n}</button>`
  }).join('')
  return `<div class="${GROUP_CLS}"><span class="${GROUP_LABEL_CLS}">质量</span><div class="flex flex-wrap gap-1 flex-1">${btns}</div></div>`
}

function tagGroupHtml(list): string {
  const tagFacets = FilterEngine.buildTagFacets(list, baseQuery(), filterContext(), TAG_FACET_LIMIT)
  const shown = new Map(tagFacets.map((f) => [f.tag, f.count]))
  // 选中的标签即使掉出 TopN 也始终展示
  state.activeTags.forEach((t) => {
    if (!shown.has(t)) shown.set(t, 0)
  })
  if (shown.size === 0) return ''
  const btns = Array.from(shown.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(
      ([tag, count]) =>
        `<button class="${CHIP_CLS}${state.activeTags.has(tag) ? ' active' : ''}" data-kind="tag" data-value="${escapeHtml(tag)}">${escapeHtml(tag)} ${count}</button>`
    )
    .join('')
  return `<div class="${GROUP_CLS}"><span class="${GROUP_LABEL_CLS}">标签</span><div class="flex flex-wrap gap-1 flex-1">${btns}</div></div>`
}

function hasExtraFilters(scope: 'gallery' | 'toolbox'): boolean {
  // 主题/质量分是画廊专属维度，不参与工具箱的「清除筛选」显示判定
  if (scope === 'gallery' && (state.activeTheme !== 'all' || state.minQuality > 0)) return true
  return state.activeRunStatus !== 'all' || state.activeTags.size > 0
}

function renderHost(host: HTMLElement, scope: 'gallery' | 'toolbox'): void {
  if (!state.examples || state.examples.length === 0) {
    host.innerHTML = ''
    return
  }
  const list = scope === 'toolbox' ? state.examples.filter((e) => e.category === 'tools') : state.examples
  const groups = [statusGroupHtml()]
  if (scope === 'gallery') {
    const counts = computeCounts(list)
    groups.push(themeGroupHtml(counts), qualityGroupHtml(counts))
  }
  const tagHtml = tagGroupHtml(list)
  if (tagHtml) groups.push(tagHtml)
  if (hasExtraFilters(scope)) {
    groups.push(
      '<button class="facet-clear self-start border-0 bg-transparent text-ink-mute text-[11px] cursor-pointer py-0.5 underline hover:text-ink" data-kind="clear">清除筛选</button>'
    )
  }
  host.innerHTML = groups.join('')
}

export function renderFacets(): void {
  if (els.galleryFacets) renderHost(els.galleryFacets, 'gallery')
  if (els.toolboxFacets) renderHost(els.toolboxFacets, 'toolbox')
}

export function initFacets(): void {
  for (const host of [els.galleryFacets, els.toolboxFacets]) {
    if (!host) continue
    host.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('.facet-chip, .facet-clear') as HTMLElement | null
      if (!btn) return
      const kind = btn.dataset.kind
      if (kind === 'status') {
        state.activeRunStatus = btn.dataset.value as any
      } else if (kind === 'theme') {
        state.activeTheme = btn.dataset.value || 'all'
        persistViewPrefs()
      } else if (kind === 'quality') {
        state.minQuality = Number(btn.dataset.value) || 0
        persistViewPrefs()
      } else if (kind === 'tag') {
        const tag = btn.dataset.value || ''
        if (state.activeTags.has(tag)) state.activeTags.delete(tag)
        else state.activeTags.add(tag)
      } else if (kind === 'clear') {
        state.activeRunStatus = 'all'
        state.activeTags.clear()
        state.activeTheme = 'all'
        state.minQuality = 0
        persistViewPrefs()
      }
      applyAllFilters()
    })
  }
}
