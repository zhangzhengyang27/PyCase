// store.ts：Vue 渲染层共享状态（组合式单例，无 Pinia 依赖）
// 迁移自旧 app.ts/state.ts 的编排职责：示例加载、筛选查询组装、收藏/历史/偏好持久化。
// 与旧实现的本质差异：派生数据（filtered/facets/计数）全部是 computed——
// 状态变化自动重算，从架构上消灭旧版"手动 applyAllFilters 同步视图"的整类 bug。
// 纯过滤逻辑仍全部来自 filter-engine.ts（与旧窗口共用同一实现与测试）。

import { computed, ref, watch } from 'vue'
import * as FilterEngine from '../src/filter-engine'
import { THEMES } from '../src/themes'
import type { ExampleItem, RunHistoryEntry } from '../src/state'
import { api } from '../src/sidecar-client'

// 画廊/工具箱共用的示例类型（sidecar list_examples 序列化 + 筛选预处理缓存）
export interface VExample extends ExampleItem, FilterEngine.ExampleLike {
  title?: string
  description?: string
  _codeLower?: string
  _tagsAll?: string[]
}

export type SortBy = 'quality_desc' | 'name' | 'last_run'
export type ViewKey = 'gallery' | 'toolbox'

// ---------------------------------------------------------------------------
// 响应式状态
// ---------------------------------------------------------------------------
export const loading = ref(false)
export const loadError = ref('')
export const examples = ref<VExample[]>([])

// 视图
export const activeView = ref<ViewKey>('gallery')
export const searchQuery = ref('')
export const toolSearchQuery = ref('')

// 画廊筛选维度
export const activeTheme = ref('all')
export const minQuality = ref(0)
export const sortBy = ref<SortBy>('quality_desc')
export const galleryLimit = ref(120)

// 收藏 / 运行状态 / 标签
export const favorites = ref(new Set<string>())
export const favOnly = ref(false)
export const activeRunStatus = ref<'all' | 'ok' | 'failed' | 'never'>('all')
export const activeTags = ref(new Set<string>())
export const runHistory = ref<RunHistoryEntry[]>([])

// 搜索防抖：输入框即时回显，筛选应用延迟 120ms（旧版 150ms 防抖的等价物，
// 差别在于旧版防的是全量 innerHTML 重建，这里防的是大集合上的谓词扫描）
let _galleryTimer: ReturnType<typeof setTimeout> | undefined
let _toolboxTimer: ReturnType<typeof setTimeout> | undefined
const appliedSearch = ref('')
const appliedToolSearch = ref('')
watch(searchQuery, (v) => {
  clearTimeout(_galleryTimer)
  _galleryTimer = setTimeout(() => (appliedSearch.value = v), 120)
})
watch(toolSearchQuery, (v) => {
  clearTimeout(_toolboxTimer)
  _toolboxTimer = setTimeout(() => (appliedToolSearch.value = v), 120)
})

// ---------------------------------------------------------------------------
// 主题谓词表（静态，构建一次）
// ---------------------------------------------------------------------------
const THEME_MATCHERS: Record<string, (e: ExampleItem) => boolean> = Object.fromEntries(
  THEMES.map((t) => [t.key, t.filter as (e: ExampleItem) => boolean])
)

// ---------------------------------------------------------------------------
// 筛选上下文与查询（computed：依赖变化自动重建，无需手动刷新索引）
// ---------------------------------------------------------------------------
const runStatusIndex = computed(() => FilterEngine.buildRunStatusIndex(runHistory.value))
const lastRunIndex = computed(() => FilterEngine.buildLastRunIndex(runHistory.value))

const filterContext = computed<FilterEngine.FilterContext>(() => ({
  favorites: favorites.value,
  runStatus: runStatusIndex.value,
  themeMatchers: THEME_MATCHERS,
  lastRunAt: lastRunIndex.value
}))

const galleryQuery = computed<FilterEngine.FilterQuery>(() => ({
  favOnly: favOnly.value,
  runStatus: activeRunStatus.value,
  theme: activeTheme.value,
  minQuality: minQuality.value,
  tags: Array.from(activeTags.value),
  q: appliedSearch.value
}))

const toolboxQuery = computed<FilterEngine.FilterQuery>(() => ({
  category: 'tools',
  favOnly: favOnly.value,
  runStatus: activeRunStatus.value,
  tags: Array.from(activeTags.value),
  q: appliedToolSearch.value
}))

/** 计数基准：剥离 theme/quality/tags 自身维度（与旧 facets.ts 口径一致） */
const countBaseQuery = computed<FilterEngine.FilterQuery>(() => ({
  ...galleryQuery.value,
  tags: [],
  theme: 'all',
  minQuality: 0
}))

// ---------------------------------------------------------------------------
// 派生数据（旧版 renderGalleryGrid / renderToolboxGrid / renderFacets 的数据部分）
// ---------------------------------------------------------------------------
export const filtered = computed(() => FilterEngine.filterExamples(examples.value, galleryQuery.value, filterContext.value))

export const sortedGallery = computed(() =>
  FilterEngine.sortExamples(filtered.value, sortBy.value, { lastRunAt: lastRunIndex.value })
)

export const shownGallery = computed(() => sortedGallery.value.slice(0, galleryLimit.value))

export const toolboxItems = computed(() => FilterEngine.filterExamples(examples.value, toolboxQuery.value, filterContext.value))

export const toolsTotal = computed(() => examples.value.filter((e) => e.category === 'tools').length)

export interface FacetCounts {
  themeCounts: Map<string, number>
  qualityCounts: Map<number, number>
}

const QUALITY_FACETS = [0, 90, 80, 60]

export const facetCounts = computed<FacetCounts>(() => {
  const themeCounts = new Map<string, number>()
  const qualityCounts = new Map<number, number>()
  const ctx = filterContext.value
  for (const ex of examples.value) {
    if (!FilterEngine.matchExample(ex, countBaseQuery.value, ctx)) continue
    for (const t of THEMES) {
      if (t.filter(ex)) themeCounts.set(t.key, (themeCounts.get(t.key) || 0) + 1)
    }
    for (const min of QUALITY_FACETS) {
      if (min === 0) continue
      if ((ex.quality_score ?? 0) >= min) qualityCounts.set(min, (qualityCounts.get(min) || 0) + 1)
    }
  }
  return { themeCounts, qualityCounts }
})

/** 标签 facet：TopN + 已选中标签保底展示（选中掉出 TopN 时计数 0 仍显示） */
export function tagFacets(list: FilterEngine.ExampleLike[], baseQuery: FilterEngine.FilterQuery): FilterEngine.TagFacet[] {
  const facets = FilterEngine.buildTagFacets(list, baseQuery, filterContext.value, 15)
  const shown = new Map(facets.map((f) => [f.tag, f.count]))
  activeTags.value.forEach((t) => {
    if (!shown.has(t)) shown.set(t, 0)
  })
  return Array.from(shown, ([tag, count]) => ({ tag, count })).sort(
    (a, b) => b.count - a.count || a.tag.localeCompare(b.tag)
  )
}

// ---------------------------------------------------------------------------
// 动作
// ---------------------------------------------------------------------------
export async function loadAll(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    const [history, favs, prefs] = await Promise.all([
      api.storeGet('history').catch(() => null),
      api.storeGet('favorites').catch(() => null),
      api.storeGet('viewPrefs').catch(() => null)
    ])
    runHistory.value = Array.isArray(history) ? history : []
    favorites.value = new Set(Array.isArray(favs) ? favs.map(String) : [])
    applyViewPrefs(prefs)

    const result = (await api.listExamples()) as { examples?: VExample[] }
    // 一次性建立筛选预处理缓存（与旧 app.ts loadExamples 相同口径）
    const list = result.examples || []
    for (const ex of list) {
      ex._importTags = FilterEngine.extractImportTags(ex.code || '')
      ex._codeLower = (ex.code || '').toLowerCase()
      ex._tagsAll = FilterEngine.allTagsOf(ex)
    }
    examples.value = list
  } catch (err) {
    loadError.value = (err as Error).message
    examples.value = []
  } finally {
    loading.value = false
  }
}

function applyViewPrefs(prefs: unknown): void {
  if (!prefs || typeof prefs !== 'object') return
  const p = prefs as Record<string, unknown>
  if (typeof p.sortBy === 'string' && ['quality_desc', 'name', 'last_run'].includes(p.sortBy)) {
    sortBy.value = p.sortBy as SortBy
  }
  // activeTheme 必须是 THEMES 的合法 key（脏数据会让引擎静默放行全部）
  if (typeof p.activeTheme === 'string' && THEMES.some((t) => t.key === p.activeTheme)) {
    activeTheme.value = p.activeTheme
  }
  if (typeof p.minQuality === 'number' && p.minQuality >= 0) minQuality.value = p.minQuality
}

export function persistViewPrefs(): void {
  api.storeSet('viewPrefs', { sortBy: sortBy.value, activeTheme: activeTheme.value, minQuality: minQuality.value }).catch(() => {})
}

export function toggleFavorite(id: string | undefined): boolean {
  if (!id) return false
  const next = new Set(favorites.value)
  const faved = !next.has(id)
  if (faved) next.add(id)
  else next.delete(id)
  favorites.value = next // 整体替换触发依赖更新（Set 内部变更同样被追踪，替换语义更直白）
  api.storeSet('favorites', Array.from(next)).catch(() => {})
  return faved
}

export function isFavorite(id: string | undefined): boolean {
  return !!id && favorites.value.has(id)
}

export function clearFilters(): void {
  activeRunStatus.value = 'all'
  activeTags.value = new Set()
  activeTheme.value = 'all'
  minQuality.value = 0
  persistViewPrefs()
}


// ---------------------------------------------------------------------------
// 详情页 / 输出面板兼容导出（v0.10 组件契约；旧 Vue 渲染层与主渲染层对齐）
// ---------------------------------------------------------------------------
export const selectedId = ref<string | null>(null)
export const originalCode = ref('')
export const isDirty = ref(false)

export function registerEditor(_editor: unknown): void {
  /* 旧渲染层占位：Monaco 生命周期由组件自行管理 */
}

export function onEditorContentChanged(code: string): void {
  if (selectedId.value) isDirty.value = code !== originalCode.value
}

export interface OutputLine {
  text: string
  cls: string
}

export const outputLines = ref<OutputLine[]>([])
export const outputTruncated = ref(false)
export const outputImages = ref<{ url: string; name: string }[]>([])
export const outputDot = computed(() => 'inline-block w-2 h-2 rounded-full shrink-0 bg-ink-faint')

export function clearOutput(): void {
  outputLines.value = []
  outputImages.value = []
  outputTruncated.value = false
}

export async function downloadImage(url: string, name: string): Promise<void> {
  try {
    const res = (await api.downloadResultImage(url, name)) as { error?: string }
    if (res && res.error) loadError.value = res.error
  } catch (err) {
    loadError.value = (err as Error).message
  }
}

// $persist：模板里的可选持久化钩子（旧渲染层占位实现）
declare module 'vue' {
  interface ComponentCustomProperties {
    $persist?: () => void
  }
}


// ---------------------------------------------------------------------------
// 详情页 / 参数表单 / 资产面板 / 历史面板兼容导出（v0.10 组件契约）。
// 旧 Vue 渲染层（迁移期保留）的组件按这些名字取状态；实现与主渲染层
// store.ts 对齐，仅与旧层内部状态联动的部分为占位实现。
// ---------------------------------------------------------------------------
export interface ArgSpec {
  name: string
  flags: string[]
  dest: string
  type: string
  default?: unknown
  help?: string
  choices?: unknown[]
  required?: boolean
  action?: string
  is_positional?: boolean
  nargs?: string | number | null
  metavar?: string | null
}

export const argsLoading = ref(false)
export const currentArgs = ref<ArgSpec[]>([])
export const pendingBackfillTokens = ref<string[] | null>(null)

let _argsCollector: (() => string[]) | null = null

export function registerArgsCollector(collect: (() => string[]) | null): void {
  _argsCollector = collect
}

export const requiredArgsMissing = computed(() => {
  void _argsCollector
  return [] as string[]
})

export const selectedExample = computed(() => examples.value.find((e) => e.id === selectedId.value) || null)
export const isRunning = ref(false)
export const saving = ref(false)
export const runStatusText = ref('就绪')

export function closeDetail(): void {
  selectedId.value = null
}

export function saveExample(): void {
  /* 旧渲染层占位：保存链路由主渲染层承载 */
}

export function stopRun(): void {
  /* 旧渲染层占位 */
}

export function runFromDetail(): void {
  /* 旧渲染层占位 */
}

export interface AssetInfo {
  filename: string
  size: number
  modified: number
  is_image: boolean
}

export const assets = ref<AssetInfo[]>([])
export const assetsLoading = ref(false)

export function uploadAssets(_id: string, _files: File[]): void {
  /* 旧渲染层占位 */
}

export function deleteAsset(_name: string): void {
  /* 旧渲染层占位 */
}

export function rerunEntry(_entry: RunHistoryEntry): void {
  /* 旧渲染层占位 */
}

export const detailHistory = computed(() =>
  selectedId.value ? runHistory.value.filter((h) => h.id === selectedId.value) : []
)
