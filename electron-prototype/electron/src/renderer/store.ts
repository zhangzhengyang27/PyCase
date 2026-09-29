// store.ts：Vue 渲染层共享状态（组合式单例，无 Pinia 依赖）
// 迁移自旧 app.ts/state.ts 的编排职责：示例加载、筛选查询组装、收藏/历史/偏好持久化。
// 与旧实现的本质差异：派生数据（filtered/facets/计数）全部是 computed——
// 状态变化自动重算，从架构上消灭旧版"手动 applyAllFilters 同步视图"的整类 bug。
// 纯过滤逻辑仍全部来自 filter-engine.ts（与旧窗口共用同一实现与测试）。

import { computed, reactive, ref, shallowRef, watch } from 'vue'
import { pushToast } from './toast'
import * as FilterEngine from './src/filter-engine'
import { splitArgs } from './src/utils'
import { THEMES } from './src/themes'
import { invalidateExampleVisual } from './src/overview'
import { buildFilterChips, type FilterChip } from './src/filter-chips'
import type { ExampleItem, RunHistoryEntry } from './src/types'
import { api } from './src/sidecar-client'

// 画廊/工具箱共用的示例类型（sidecar list_examples 序列化 + 筛选预处理缓存）
export interface VExample extends ExampleItem, FilterEngine.ExampleLike {
  title?: string
  description?: string
  _codeLower?: string
  _tagsAll?: string[]
}

export type SortBy = 'quality_desc' | 'name' | 'last_run'
export type ViewKey = 'gallery' | 'toolbox' | 'runner'
/** 浏览密度：网格卡墙 / 单行清单 */
export type ViewDensity = 'grid' | 'list'

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

// 画廊两级浏览：总览（主题分区落地页）→ 下钻浏览（侧栏 + 结果条 + 网格/清单）。
// galleryMode 不持久化——落地页是每次打开应用的默认起点
export const galleryMode = ref<'overview' | 'browse'>('overview')

// 画廊筛选维度
export const activeTheme = ref('all')
export const minQuality = ref(0)
export const sortBy = ref<SortBy>('quality_desc')
export const galleryLimit = ref(120)
// 总览标签分区/项目区下钻的会话级范围（不持久化，与 activeTags 同策略）；
// tagsAny 在引擎内为 OR 语义（分区 = 一组同义标签），与侧栏多选 tags 的 AND 互不干扰
export const activeSectionTags = ref<string[]>([])
export const activeCategory = ref<'all' | 'projects'>('all')

// 浏览密度（画廊浏览态网格/清单，随 viewPrefs 持久化）
export const viewMode = ref<ViewDensity>('grid')

// 收藏 / 运行状态 / 可运行性 / 标签
export const favorites = ref(new Set<string>())
export const favOnly = ref(false)
export const activeRunStatus = ref<'all' | 'ok' | 'failed' | 'never'>('all')
export const activeRunnable = ref<FilterEngine.RunnableFilter>('all')
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
  runnable: activeRunnable.value,
  theme: activeTheme.value,
  minQuality: minQuality.value,
  tags: Array.from(activeTags.value),
  tagsAny: activeSectionTags.value,
  category: activeCategory.value,
  q: appliedSearch.value
}))

const toolboxQuery = computed<FilterEngine.FilterQuery>(() => ({
  category: 'tools',
  favOnly: favOnly.value,
  runStatus: activeRunStatus.value,
  runnable: activeRunnable.value,
  tags: Array.from(activeTags.value),
  q: appliedToolSearch.value
}))

/** 计数基准：剥离 theme/quality/tags 自身维度（与旧 facets.ts 口径一致）；
 *  分区范围（tagsAny/category）同 theme 一样剥离——侧栏 facet 计数不随下钻范围缩放 */
const countBaseQuery = computed<FilterEngine.FilterQuery>(() => ({
  ...galleryQuery.value,
  tags: [],
  tagsAny: [],
  category: 'all',
  theme: 'all',
  minQuality: 0
}))

// ---------------------------------------------------------------------------
// 派生数据（旧版 renderGalleryGrid / renderToolboxGrid / renderFacets 的数据部分）
// ---------------------------------------------------------------------------
/** 画廊池：工具只待在工具箱——画廊（总览分区/浏览筛选/侧栏 facet）一律不含 tools，
 *  与工具箱查询的 category:'tools' 互为补集 */
export const galleryExamples = computed<VExample[]>(() => examples.value.filter((e) => e.category !== 'tools'))

export const filtered = computed(() => FilterEngine.filterExamples(galleryExamples.value, galleryQuery.value, filterContext.value) as VExample[])

export const sortedGallery = computed(() =>
  FilterEngine.sortExamples(filtered.value, sortBy.value, { lastRunAt: lastRunIndex.value }) as VExample[]
)

export const shownGallery = computed(() => sortedGallery.value.slice(0, galleryLimit.value))

export const toolboxItems = computed(() => FilterEngine.filterExamples(examples.value, toolboxQuery.value, filterContext.value) as VExample[])

export const toolsTotal = computed(() => examples.value.filter((e) => e.category === 'tools').length)

/** 视图内排序助手：工具箱分组、画廊等共用同一排序偏好（含最近运行索引） */
export function sortVExamples(list: VExample[]): VExample[] {
  return FilterEngine.sortExamples(list, sortBy.value, { lastRunAt: lastRunIndex.value }) as VExample[]
}

export interface FacetCounts {
  themeCounts: Map<string, number>
  qualityCounts: Map<number, number>
  runnableCounts: Map<string, number>
}

const QUALITY_FACETS = [0, 90, 80, 60]
const RUNNABLE_FACET_KEYS = ['runnable', 'missing_deps', 'empty', 'broken', 'risky']

export const facetCounts = computed<FacetCounts>(() => {
  const themeCounts = new Map<string, number>()
  const qualityCounts = new Map<number, number>()
  const runnableCounts = new Map<string, number>()
  const ctx = filterContext.value
  for (const ex of galleryExamples.value) {
    if (!FilterEngine.matchExample(ex, countBaseQuery.value, ctx)) continue
    for (const t of THEMES) {
      if (t.filter(ex)) themeCounts.set(t.key, (themeCounts.get(t.key) || 0) + 1)
    }
    for (const min of QUALITY_FACETS) {
      if (min === 0) continue
      if ((ex.quality_score ?? 0) >= min) qualityCounts.set(min, (qualityCounts.get(min) || 0) + 1)
    }
    for (const key of RUNNABLE_FACET_KEYS) {
      if (ex.run_status === key) runnableCounts.set(key, (runnableCounts.get(key) || 0) + 1)
    }
  }
  return { themeCounts, qualityCounts, runnableCounts }
})

const toolboxFacetBase = computed<FilterEngine.FilterQuery>(() => ({ ...toolboxQuery.value, tags: [] }))

/** 标签 facet：TopN + 已选中标签保底展示（选中掉出 TopN 时计数 0 仍显示）。
 *  基准查询按视图取各自搜索词（旧版工具箱误用画廊搜索词，此处为有意修正）。 */
export function tagFacetsFor(scope: 'gallery' | 'toolbox'): FilterEngine.TagFacet[] {
  const list = scope === 'toolbox' ? toolboxItems.value : galleryExamples.value
  const base = scope === 'toolbox' ? toolboxFacetBase.value : countBaseQuery.value
  return buildTagFacetsCached(list, base)
}

function buildTagFacetsCached(list: VExample[], baseQuery: FilterEngine.FilterQuery): FilterEngine.TagFacet[] {
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
    const [history, favs, prefs, safety, runPrefs] = await Promise.all([
      api.storeGet('history').catch(() => null),
      api.storeGet('favorites').catch(() => null),
      api.storeGet('viewPrefs').catch(() => null),
      api.storeGet('safetyPrefs').catch(() => null),
      api.storeGet('runPrefs').catch(() => null)
    ])
    runHistory.value = Array.isArray(history) ? (history as RunHistoryEntry[]) : []
    favorites.value = new Set(Array.isArray(favs) ? (favs as unknown[]).map(String) : [])
    applyViewPrefs(prefs)
    skipHighRiskConfirm.value = !!(safety as Record<string, unknown> | null)?.skipHighRiskConfirm
    if (runPrefs && typeof (runPrefs as Record<string, unknown>).timeout === 'number') {
      const t = (runPrefs as Record<string, unknown>).timeout as number
      if (t >= 5 && t <= 600) runTimeout.value = t
    }

    const result = (await api.listExamples()) as { examples?: VExample[] }
    // 一次性建立筛选预处理缓存（与旧 app.ts loadExamples 相同口径）
    const list = result.examples || []
    for (const ex of list) {
      // v2：import 标签用服务端下发的派生事实；列表不含 code，故不再从 code 反推
      ex._importTags = Array.isArray(ex.import_tags) ? ex.import_tags : []
      ex._codeLower = ''
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
  if (p.viewMode === 'grid' || p.viewMode === 'list') viewMode.value = p.viewMode
}

export function persistViewPrefs(): void {
  api
    .storeSet('viewPrefs', {
      sortBy: sortBy.value,
      activeTheme: activeTheme.value,
      minQuality: minQuality.value,
      viewMode: viewMode.value
    })
    .catch(() => {})
}

export function toggleFavorite(id: string | undefined): boolean {
  if (!id) return false
  const next = new Set(favorites.value)
  const faved = !next.has(id)
  if (faved) next.add(id)
  else next.delete(id)
  favorites.value = next // 整体替换触发依赖更新（Set 内部变更同样被追踪，替换语义更直白）
  api.storeSet('favorites', Array.from(next)).catch(() => {})
  // 不弹 toast：星标本身已是即时状态反馈，连点收藏时右下角会刷屏
  return faved
}

export function isFavorite(id: string | undefined): boolean {
  return !!id && favorites.value.has(id)
}

export function clearFilters(): void {
  activeRunStatus.value = 'all'
  activeRunnable.value = 'all'
  activeTags.value = new Set()
  activeTheme.value = 'all'
  minQuality.value = 0
  activeSectionTags.value = []
  activeCategory.value = 'all'
  persistViewPrefs()
}

// ---------------------------------------------------------------------------
// 浏览态结果条：筛选芯片 + 两级浏览入口
// ---------------------------------------------------------------------------
export const galleryChips = computed<FilterChip[]>(() => buildFilterChips(galleryQuery.value))

/** 移除单个芯片 = 反向应用该维度的默认值（搜索词清输入框，防抖后 applied 随之清空） */
export function removeChip(chip: FilterChip): void {
  switch (chip.key) {
    case 'fav':
      favOnly.value = false
      break
    case 'runStatus':
      activeRunStatus.value = 'all'
      break
    case 'runnable':
      activeRunnable.value = 'all'
      break
    case 'theme':
      activeTheme.value = 'all'
      persistViewPrefs()
      break
    case 'tagsAny':
      activeSectionTags.value = []
      break
    case 'category':
      activeCategory.value = 'all'
      break
    case 'quality':
      minQuality.value = 0
      persistViewPrefs()
      break
    case 'tag': {
      const next = new Set(activeTags.value)
      next.delete(chip.value)
      activeTags.value = next
      break
    }
    case 'q':
      searchQuery.value = ''
      break
  }
}

/** 清空全部筛选（含收藏开关与两个搜索框）；芯片区「清空」与侧栏共用语义超集 */
export function clearAllFilters(): void {
  clearFilters()
  favOnly.value = false
  searchQuery.value = ''
  toolSearchQuery.value = ''
}

/** 从总览态下钻进入浏览态，可选地预置范围（主题 / 分区标签组 / 项目类目 / 收藏）。
 *  三种范围互斥：设置其一即清空另两者（分区下钻 = 重新选择范围，避免 AND 出空集） */
export function openGalleryBrowse(preset?: { theme?: string; tags?: string[]; category?: 'projects'; favOnly?: boolean }): void {
  if (preset?.tags) {
    activeSectionTags.value = preset.tags
    activeTheme.value = 'all'
    activeCategory.value = 'all'
  } else if (preset?.category) {
    activeCategory.value = preset.category
    activeSectionTags.value = []
    activeTheme.value = 'all'
  } else if (preset?.theme) {
    activeTheme.value = preset.theme
    activeSectionTags.value = []
    activeCategory.value = 'all'
    persistViewPrefs()
  }
  if (preset?.favOnly) favOnly.value = true
  galleryMode.value = 'browse'
}

// ===========================================================================
// 详情页与运行生命周期（迁移第 3 步：参数表单 / Monaco 保存 / 运行输出 / 历史 / 资源）
// ===========================================================================

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

export interface OutputLine {
  text: string
  cls: 'base' | 'system' | 'error' | 'success'
}

export interface OutputImage {
  url: string
  name: string
}

export interface AssetInfo {
  filename: string
  size: number
  modified: number
  is_image: boolean
}

const MAX_OUTPUT_LINES = 5000
const HISTORY_CAP = 500
// 详情态
export const selectedId = ref<string | null>(null)
export const originalCode = ref('')
export const isDirty = ref(false)
export const saving = ref(false)
export const currentArgs = ref<ArgSpec[]>([])
export const argsLoading = ref(false)
// 参数回填令牌（历史重跑）：ArgsForm 在参数装载完成后消费
export const pendingBackfillTokens = ref<string[] | null>(null)

// 运行态（同窗口同时刻至多一个运行；输出汇固定 detail，运行器视图步骤 4 迁移）
export const isRunning = ref(false)
export const currentRunId = ref<string | null>(null)
export const currentRunMeta = ref<{ id: string; name: string; args: string[]; startedAt: number } | null>(null)
export const runStatusText = ref('就绪')
/** 运行超时（秒）：超时强制终止；设置弹窗「运行」分区可调，存 runPrefs */
export const runTimeout = ref(30)
export const runSink = ref<OutputSurface>('detail')
export type OutputSurface = 'detail' | 'runner'
export type OutputDot = 'idle' | 'running' | 'success' | 'error'
export interface SurfaceState {
  lines: OutputLine[]
  images: OutputImage[]
  dot: OutputDot
  truncated: boolean
}
const surfaces = reactive<Record<OutputSurface, SurfaceState>>({
  detail: { lines: [], images: [], dot: 'idle', truncated: false },
  runner: { lines: [], images: [], dot: 'idle', truncated: false }
})
export function surfaceState(s: OutputSurface): SurfaceState {
  return surfaces[s]
}
// run_id 回包到达前产生的早期输出缓冲（旧实现此处会丢行，这里补上）
let _earlyOutputBuffer: OutputLine[] = []

// 资源
export const assets = ref<AssetInfo[]>([])
export const assetsLoading = ref(false)

export const selectedExample = computed(() => examples.value.find((e) => e.id === selectedId.value) || null)
export const detailHistory = computed(() =>
  selectedId.value ? runHistory.value.filter((h) => h.id === selectedId.value).slice(0, 20) : []
)
/**
 * 参数是否「既没有默认值、也没有用户填的值」。
 *
 * 注意 sidecar 对**没有**默认值的参数返回 `"default": null`（不是省略、也不是 undefined），
 * 所以这里必须同时判 null 与 undefined —— 只判 `=== undefined` 会让整个必填门禁永远为假
 * （曾经如此：提示文案、字段红框、runFromCard 的拦截全是死代码）。
 */
function isRequiredArgUnset(a: ArgSpec): boolean {
  const noDefault = a.default === undefined || a.default === null
  return !!a.required && noDefault && a.action !== 'store_true' && a.action !== 'store_false'
}

// 表单值（用户已填的内容）存在 ArgsForm 组件局部的 reactive 里，store 侧读不到，
// 因此由表单反向注册一个「按当前值判断是否仍缺必填项」的校验器。
// 未注册时（例如详情页未挂载表单）回退到纯 spec 判定。
const _argsValidator = shallowRef<(() => boolean) | null>(null)

export function registerArgsValidator(fn: (() => boolean) | null): void {
  _argsValidator.value = fn
}

/**
 * 是否存在「必填但没有值」的参数。
 * 「有默认值」即视为已满足——必填不等于「必须由用户输入」（见 isRequiredArgUnset）。
 */
export const requiredArgsMissing = computed(() =>
  _argsValidator.value ? _argsValidator.value() : currentArgs.value.some(isRequiredArgUnset)
)

function appendOutput(text: string, cls: OutputLine['cls'] = 'base', surface: OutputSurface = 'detail'): void {
  const state = surfaces[surface]
  const lines = state.lines
  if (lines.length >= MAX_OUTPUT_LINES) {
    const removeCount = Math.floor(MAX_OUTPUT_LINES * 0.1)
    lines.splice(0, removeCount)
    if (!state.truncated) {
      state.truncated = true
      lines.unshift({ text: `[系统] 输出超过 ${MAX_OUTPUT_LINES} 行，已自动截断，仅保留最近的输出`, cls: 'system' })
    }
  }
  lines.push({ text, cls })
}

function resetOutputSurface(surface: OutputSurface): void {
  const state = surfaces[surface]
  state.lines = []
  state.images = []
  state.truncated = false
  state.dot = 'running'
}

export function clearSurface(surface: OutputSurface): void {
  const state = surfaces[surface]
  state.lines = []
  state.images = []
  state.truncated = false
  state.dot = 'idle'
  if (!isRunning.value) runStatusText.value = '就绪'
}

/** 打开详情页：返回参数解析 Promise（卡片「运行」据此决定自动运行或引导填参） */
export async function openDetail(id: string): Promise<ArgSpec[]> {
  const ex = examples.value.find((e) => e.id === id)
  if (!ex) return []
  // 未保存的编辑不得静默丢弃：切换到不同示例前需要确认
  if (selectedId.value && selectedId.value !== id && isDirty.value && !window.confirm('当前示例有未保存的修改，丢弃并继续？')) {
    return []
  }
  if (selectedId.value !== id) {
    selectedId.value = id
    originalCode.value = ex.code || ''
    isDirty.value = false
    resetOutputSurface('detail')
    runStatusText.value = '就绪'
    assets.value = []
  }
  // 参数解析与资源列表并行；带序号防过期响应（旧版竞态的响应式等价物）
  const seq = ++_openDetailSeq
  argsLoading.value = true
  const argsPromise = (async () => {
    try {
      const result = (await api.parseArgs(id)) as { args?: ArgSpec[] }
      if (seq !== _openDetailSeq) return []
      currentArgs.value = result.args || []
    } catch (err) {
      console.error('解析参数失败:', err)
      if (seq !== _openDetailSeq) return []
      currentArgs.value = []
    } finally {
      if (seq === _openDetailSeq) argsLoading.value = false
    }
    return currentArgs.value
  })()
  void loadAssets(id)
  return argsPromise
}
let _openDetailSeq = 0

export function closeDetail(): void {
  if (isDirty.value && !window.confirm('当前示例有未保存的修改，丢弃并返回？')) return
  selectedId.value = null
}

// Monaco 实例由组件注册进来；内容变更与取值都经它
let _editor: { getValue: () => string; setValue: (v: string) => void; getSelectedText?: () => string } | null = null
let _argsCollector: (() => string[]) | null = null
let _argsSetter: ((idx: number, v: string) => void) | null = null

export function registerEditor(editor: typeof _editor): void {
  _editor = editor
}
export function registerArgsCollector(fn: (() => string[]) | null): void {
  _argsCollector = fn
}
export function registerArgsSetter(fn: ((idx: number, v: string) => void) | null): void {
  _argsSetter = fn
}

export function onEditorContentChanged(code: string): void {
  if (selectedId.value) isDirty.value = code !== originalCode.value
}

export async function saveExample(): Promise<void> {
  const id = selectedId.value
  if (!id || !isDirty.value || saving.value || !_editor) return
  const newCode = _editor.getValue()
  saving.value = true
  try {
    const result = (await api.saveExample(id, newCode)) as { json_file?: string; path?: string }
    // 保存期间可能已切换示例：只允许写回保存时那个示例的状态
    if (selectedId.value !== id) return
    originalCode.value = newCode
    isDirty.value = false
    const ex = examples.value.find((e) => e.id === id)
    if (ex) {
      ex.code = newCode
      // 同步重建筛选预处理缓存与参数解析（argparse 定义可能变化）
      ex._importTags = FilterEngine.extractImportTags(newCode)
      ex._codeLower = newCode.toLowerCase()
      ex._tagsAll = FilterEngine.allTagsOf(ex)
      invalidateExampleVisual(ex)
      void openDetail(id) // 重载参数（保持选中，isDirty 已复位）
    }
    appendOutput(`[系统] 已保存: ${result.json_file || result.path || id}\n`, 'system')
    pushToast('success', '示例已保存并回写 JSON')
  } catch (err) {
    appendOutput(`[错误] 保存失败: ${(err as Error).message}\n`, 'error')
    pushToast('error', `保存失败: ${(err as Error).message}`)
  } finally {
    saving.value = false
  }
}

export function runFromDetail(): void {
  if (isRunning.value || !selectedId.value) return
  const args = _argsCollector ? _argsCollector() : []
  // 必填项确实没有值（既无 default、用户也没填）时不起跑：collectArgs 已在上面置错
  // 并聚焦首个缺失字段，这里只负责拦住这次运行。有默认值的必填项不会被拦。
  if (requiredArgsMissing.value) return
  void startRun(selectedId.value, args, 'detail')
}

/** 卡片「运行」入口：必填参数缺失则留在表单引导填写，否则按表单值自动运行 */
export async function runFromCard(id: string): Promise<void> {
  const args = await openDetail(id)
  if (selectedId.value !== id) return // 等待期间用户已切换
  if (requiredArgsMissing.value) return
  runFromDetail()
}

// ---------------------------------------------------------------------------
// 高危运行前确认（安全兜底）：risk_high 示例在真正发起运行前必须经过确认弹窗。
// 卡片/详情页/运行器/历史重跑四个入口全部汇聚于 startRun，此处单点守卫全覆盖。
// sidecar 的子进程隔离不是沙箱：确认弹窗展示扫描到的危险调用明细。
// ---------------------------------------------------------------------------
export const pendingHighRiskRun = ref<{ id: string; args: string[]; sink: OutputSurface } | null>(null)
export const skipHighRiskConfirm = ref(false)

/** 高危确认开关（设置弹窗「安全」分区）：与确认弹窗的「不再提示」共用同一持久化键 */
export function setSkipHighRiskConfirm(skip: boolean): void {
  skipHighRiskConfirm.value = skip
  api.storeSet('safetyPrefs', { skipHighRiskConfirm: skip }).catch(() => {})
}

export function resolveHighRiskRun(proceed: boolean, skip: boolean): void {
  const pending = pendingHighRiskRun.value
  pendingHighRiskRun.value = null
  if (skip && pending) setSkipHighRiskConfirm(true)
  if (pending && proceed) void beginRun(pending.id, pending.args, pending.sink)
}

async function startRun(id: string, args: string[], sink: OutputSurface = 'detail'): Promise<void> {
  const ex = examples.value.find((e) => e.id === id)
  if (!ex) return
  if (ex.risk_high && !skipHighRiskConfirm.value) {
    pendingHighRiskRun.value = { id, args, sink }
    return
  }
  await beginRun(id, args, sink)
}

/** 调整并持久化运行超时（秒） */
export function setRunTimeout(seconds: number): void {
  runTimeout.value = seconds
  api.storeSet('runPrefs', { timeout: seconds }).catch(() => {})
}

async function beginRun(id: string, args: string[], sink: OutputSurface = 'detail'): Promise<void> {
  const ex = examples.value.find((e) => e.id === id)
  if (!ex) return
  runSink.value = sink
  isRunning.value = true
  resetOutputSurface(sink)
  runStatusText.value = '运行中…'
  appendOutput(`▶ 运行: ${ex.name}\n`, 'system', sink)
  if (args.length > 0) appendOutput(`  参数: ${args.join(' ')}\n`, 'system', sink)
  currentRunMeta.value = { id, name: ex.name, args, startedAt: Date.now() }
  _earlyOutputBuffer = []
  try {
    const params: { id: string; timeout: number; args?: string[] } = { id, timeout: runTimeout.value }
    if (args.length > 0) params.args = args
    const result = (await api.runExample(params)) as { run_id?: string }
    currentRunId.value = result.run_id || null
    appendOutput(`  run_id: ${currentRunId.value}\n`, 'system', sink)
    // 补放 run_id 回包前到达的早期输出
    for (const line of _earlyOutputBuffer) surfaces[runSink.value].lines.push(line)
    _earlyOutputBuffer = []
  } catch (err) {
    appendOutput(`[错误] 启动失败: ${(err as Error).message}\n`, 'error', sink)
    isRunning.value = false
    currentRunMeta.value = null
    surfaces[sink].dot = 'error'
    runStatusText.value = '启动失败'
  }
}

// ---------------------------------------------------------------------------
// 运行器视图（最基础的运行入口：名称搜索 / 只读预览 / 单行参数）
// ---------------------------------------------------------------------------
export const runnerSelectedId = ref<string | null>(null)
export const runnerArgsLine = ref('')
export const runnerQuery = ref('')
export const runnerHits = computed(() => {
  const q = runnerQuery.value.trim().toLowerCase()
  if (!q) return []
  return examples.value.filter((e) => e.name.toLowerCase().includes(q)).slice(0, 8)
})
export const runnerExample = computed(() => examples.value.find((e) => e.id === runnerSelectedId.value) || null)

export function selectRunnerExample(id: string): void {
  if (!examples.value.some((e) => e.id === id)) return
  runnerSelectedId.value = id
  runnerQuery.value = ''
}

export function runnerRun(): void {
  const ex = runnerExample.value
  if (!ex || isRunning.value) return
  startRun(ex.id, splitArgs(runnerArgsLine.value), 'runner')
}

export function clearRunnerOutput(): void {
  clearSurface('runner')
}

export async function stopRun(): Promise<void> {
  if (!currentRunId.value) return
  try {
    await api.stopRun(currentRunId.value)
    appendOutput('\n[系统] 已发送停止指令\n', 'system')
  } catch (err) {
    appendOutput(`[错误] 停止失败: ${(err as Error).message}\n`, 'error')
  }
}

/** 历史重跑：等参数装载完成后回填记录参数再运行（ArgsForm 消费回填令牌） */
export async function rerunEntry(entry: RunHistoryEntry): Promise<void> {
  if (isRunning.value) return
  const argsSpecs = await openDetail(entry.id)
  if (selectedId.value !== entry.id) return
  pendingBackfillTokens.value = entry.args || []
  if (requiredArgsMissing.value && (entry.args || []).length === 0) return
  runFromDetail()
}

// ---------------------------------------------------------------------------
// 运行事件订阅（App.vue onMounted 调用一次）
// ---------------------------------------------------------------------------
export function initRunEvents(): void {
  api.on('runOutput', (data) => {
    if (data.run_id !== currentRunId.value) {
      // run_id 回包前的早期输出进缓冲，避免丢弃
      if (isRunning.value && currentRunId.value === null) {
        _earlyOutputBuffer.push({ text: data.text || '', cls: 'base' })
      }
      return
    }
    const text = data.text || ''
    const cls: OutputLine['cls'] = text.startsWith('[系统]') || text.startsWith('[错误]') ? 'system' : 'base'
    appendOutput(text, cls, runSink.value)
  })
  api.on('runImages', (data) => {
    if (data.run_id !== currentRunId.value) return
    surfaces[runSink.value].images = (data.images || []).map((url: string) => ({
      url,
      name: decodeURIComponent(url.split('/').pop() || 'image')
    }))
  })
  api.on('runFinished', (data) => {
    if (data.run_id !== currentRunId.value) return
    const exitCode = data.exit_code
    const sink = runSink.value
    if (exitCode === 0) {
      appendOutput('✓ 运行成功 (exit code: 0)\n', 'success', sink)
      surfaces[sink].dot = 'success'
      runStatusText.value = '运行成功'
    } else {
      appendOutput(`✗ 运行失败 (exit code: ${exitCode})\n`, 'error', sink)
      surfaces[sink].dot = 'error'
      runStatusText.value = '运行失败'
    }
    if (currentRunMeta.value) recordHistory(currentRunMeta.value, exitCode)
    isRunning.value = false
    currentRunMeta.value = null
    currentRunId.value = null
  })
}

/** Vue 响应式 Proxy 不能跨 ipcRenderer.invoke 结构化克隆，IPC 传参一律深拷贝为普通对象 */
function toPlain<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function recordHistory(meta: { id: string; name: string; args: string[]; startedAt: number }, exitCode: number): void {
  const entry: RunHistoryEntry = {
    ts: new Date().toISOString(),
    id: meta.id,
    name: meta.name,
    args: meta.args,
    duration_ms: Math.max(0, Date.now() - meta.startedAt),
    exit_code: exitCode,
    ok: exitCode === 0
  }
  runHistory.value = [entry, ...runHistory.value].slice(0, HISTORY_CAP)
  void persistRunHistory()
}

function persistRunHistory(): Promise<unknown> {
  return api.storeSet('history', toPlain(runHistory.value)).catch((err) => {
    console.error('[store] 运行历史持久化失败:', err)
    return undefined
  })
}

// ---------------------------------------------------------------------------
// 资源上传 / 列举 / 删除
// ---------------------------------------------------------------------------
export async function loadAssets(id: string): Promise<void> {
  assetsLoading.value = true
  try {
    const result = (await api.listAssets(id)) as { assets?: AssetInfo[] }
    if (selectedId.value === id) assets.value = result.assets || []
  } catch {
    if (selectedId.value === id) assets.value = []
  } finally {
    assetsLoading.value = false
  }
}

export async function uploadAssets(id: string, files: File[]): Promise<void> {
  for (const file of files) {
    if (file.size > 15 * 1024 * 1024) {
      pushToast('info', `${file.name} 超过 15MB 限制`)
      continue
    }
    if (file.name.toLowerCase().endsWith('.py') || file.name.toLowerCase() === 'requirements.txt') {
      pushToast('info', `${file.name} 与示例脚本/依赖清单冲突，已拒绝`)
      continue
    }
    try {
      const buffer = await file.arrayBuffer()
      let binary = ''
      const bytes = new Uint8Array(buffer)
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
      await api.uploadAsset({ exampleId: id, fileName: file.name, data: btoa(binary) })
    } catch (err) {
      pushToast('error', `上传 ${file.name} 失败: ${(err as Error).message}`)
    }
  }
  await loadAssets(id)
}

export async function deleteAsset(filename: string): Promise<void> {
  if (!selectedId.value) return
  try {
    const result = (await api.deleteAsset({ exampleId: selectedId.value, fileName: filename })) as { assets?: AssetInfo[] }
    assets.value = result.assets || []
  } catch (err) {
    pushToast('error', `删除失败: ${(err as Error).message}`)
  }
}

export async function downloadImage(url: string, name: string): Promise<void> {
  try {
    const res = (await api.downloadResultImage(url, name)) as { canceled?: boolean; error?: string }
    if (res && res.error) pushToast('error', `下载失败：${res.error}`)
  } catch (err) {
    pushToast('error', `下载失败：${(err as Error).message}`)
  }
}


// ===========================================================================
// 环境准备状态与全局层开关（A5.5：首启引导页 / 帮助面板）
// ---------------------------------------------------------------------------
// 环境事实由 sidecar 上报（env_status + env_progress 通知），前端不猜：
// phase 推进顺序 preparing → indexing → warming → ready，失败进 failed 并带原因。
// ===========================================================================
export interface EnvStatus {
  phase: 'starting' | 'preparing' | 'indexing' | 'warming' | 'ready' | 'failed'
  /** 失败发生在哪一步（sidecar 上报；仅 phase=failed 时有意义） */
  failed_at?: 'starting' | 'preparing' | 'indexing' | 'warming'
  started_at?: number
  elapsed_ms?: number
  error?: string
  log_path?: string
  mode: 'shared' | 'system'
  venv_path?: string
  venv_ready?: boolean
  python_version?: string
  examples?: number
}

export const envStatus = ref<EnvStatus | null>(null)
export const onboardingOpen = ref(false)
export const helpOpen = ref(false)
export const appInfo = ref<{ name?: string; version?: string; electron?: string }>({})

function applyEnvStatus(next: unknown): void {
  if (next && typeof next === 'object') envStatus.value = next as EnvStatus
}

/** 订阅环境阶段推进 + 拉一次当前状态（首启页打开时补全量）。 */
export function initEnvEvents(): void {
  window.sidecar?.env?.onProgress((data) => applyEnvStatus(data))
  void refreshEnvStatus()
}

export async function refreshEnvStatus(): Promise<void> {
  try {
    applyEnvStatus(await api.envStatus())
  } catch (err) {
    console.error('[env] 读取环境状态失败:', err)
  }
}

export async function loadAppInfo(): Promise<void> {
  try {
    appInfo.value = (await api.appInfo()) as { name?: string; version?: string; electron?: string }
  } catch (err) {
    console.error('[env] 读取应用信息失败:', err)
  }
}

/** 首启引导：只在本地标记缺失时展示（首帧后，不等 sidecar ready）。 */
export async function loadOnboarding(): Promise<void> {
  try {
    const seen = (await api.storeGet('onboarding')) as { seen?: boolean } | null
    onboardingOpen.value = !seen?.seen
  } catch {
    onboardingOpen.value = true
  }
}

export async function dismissOnboarding(): Promise<void> {
  onboardingOpen.value = false
  try {
    await api.storeSet('onboarding', { seen: true, at: Date.now() })
  } catch (err) {
    console.error('[env] 写入引导标记失败:', err)
  }
}

/** 「用系统 Python 继续」：切换运行解释器模式（sidecar 侧生效，不改共享环境）。 */
export async function useSystemPython(): Promise<void> {
  try {
    applyEnvStatus(await api.setRunEnv('system'))
  } catch (err) {
    console.error('[env] 切换解释器模式失败:', err)
  }
}

/** 「重试」：重启 sidecar（其启动流程会重新预热共享环境并重发阶段事件）。 */
export async function retryEnvPrepare(): Promise<void> {
  try {
    await api.restart()
    await refreshEnvStatus()
  } catch (err) {
    console.error('[env] 重试环境准备失败:', err)
  }
}

export async function openLog(): Promise<void> {
  try {
    const r = (await api.openLog()) as { ok?: boolean; error?: string }
    if (r && r.ok === false && r.error) pushToast('error', r.error)
  } catch (err) {
    console.error('[env] 打开日志失败:', err)
  }
}

export function openHelp(): void {
  helpOpen.value = true
}
export function closeHelp(): void {
  helpOpen.value = false
}

// ===========================================================================
// 冒烟 / E2E 测试钩子：入口 HTML 带 ?smoke=1 时由 main.ts 挂到 window.__app，
// 主进程的 runSmokeTest / runE2ETest 借此驱动 Vue 应用（生产入口不注入）
// ===========================================================================
export function getTestApi(): Record<string, unknown> {
  return {
    examples: () => examples.value,
    filteredCount: () => filtered.value.length,
    // 冒烟探针从干净筛选态开始：本机 viewPrefs/runHistory 可能残留主题、搜索词等
    // 筛选状态（CI 干净环境无此问题），不清理会让 favorites/facets 断言失真
    resetViewFilters: () => {
      galleryMode.value = 'overview'
      activeTheme.value = 'all'
      minQuality.value = 0
      activeRunnable.value = 'all'
      activeRunStatus.value = 'all'
      activeTags.value = new Set()
      activeSectionTags.value = []
      activeCategory.value = 'all'
      favOnly.value = false
      searchQuery.value = ''
      toolSearchQuery.value = ''
      appliedSearch.value = ''
      appliedToolSearch.value = ''
    },
    setFavOnly: (v: boolean) => {
      favOnly.value = v
    },
    favorites: () => Array.from(favorites.value),
    toggleFavorite: (id: string) => toggleFavorite(id),
    runHistory: () => runHistory.value,
    resetRunHistory: () => {
      runHistory.value = []
    },
    recordHistory: async (meta: { id: string; name: string; args: string[]; startedAt: number }, code: number) => {
      recordHistory(meta, code)
      try {
        await api.storeSet('history', toPlain(runHistory.value))
      } catch (err) {
        return 'ERR:' + (err as Error).message
      }
      return runHistory.value.length
    },
    sortBy: () => sortBy.value,
    setSortBy: (s: 'quality_desc' | 'name' | 'last_run') => {
      sortBy.value = s
      persistViewPrefs()
    },
    setTags: (tags: string[]) => {
      activeTags.value = new Set(tags)
    },
    tagFacetsFor: (scope: 'gallery' | 'toolbox') => tagFacetsFor(scope),
    findByName: (name: string) => examples.value.find((e) => e.name === name) || null,
    openDetail: (id: string) => openDetail(id),
    selectedId: () => selectedId.value,
    currentArgs: () => currentArgs.value,
    setArgValue: (idx: number, v: string) => _argsSetter?.(idx, v),
    collectArgs: () => _argsCollector?.() || [],
    backfillArgs: (tokens: string[]) => {
      pendingBackfillTokens.value = tokens
    },
    runFromDetail: () => runFromDetail(),
    isRunning: () => isRunning.value,
    runStatusText: () => runStatusText.value,
    outputText: () => surfaces.detail.lines.map((l) => l.text).join(''),
    detailHistory: () => detailHistory.value,
    assets: () => assets.value,
    // A5.5：环境状态与全局层开关
    envStatus: () => envStatus.value,
    openHelp: () => openHelp(),
    helpOpen: () => helpOpen.value,
    onboardingOpen: () => onboardingOpen.value,
    dismissOnboarding: () => dismissOnboarding(),
    showOnboarding: () => {
      onboardingOpen.value = true
    }
  }
}

// ===========================================================================
// AI 代码解释（DeepSeek 流式；语义从旧 ai.ts 移植：设置弹窗 / 首次外发告知 /
// run_id 匹配的流式订阅 / 关面板即停止）
// ===========================================================================
export const aiSettings = reactive({
  hasKey: false,
  model: 'deepseek-chat',
  baseUrl: 'https://api.deepseek.com',
  acknowledged: false
})
export const aiRunId = ref('')
export const aiPanelOpen = ref(false)
export const aiSettingsOpen = ref(false)
export const aiStatus = ref('正在准备…')
export const aiStatusError = ref(false)
export const aiOutputText = ref('')
export const aiShowStop = ref(false)

export async function loadAISettings(): Promise<void> {
  try {
    const s = (await api.aiGetSettings()) as { hasKey?: boolean; model?: string; baseUrl?: string; acknowledged?: boolean }
    aiSettings.hasKey = !!s.hasKey
    aiSettings.model = s.model || 'deepseek-chat'
    aiSettings.baseUrl = s.baseUrl || 'https://api.deepseek.com'
    aiSettings.acknowledged = !!s.acknowledged
  } catch (err) {
    console.error('[ai] 加载设置失败:', err)
  }
}

export function openAISettings(): void {
  aiSettingsOpen.value = true
}
export function closeAISettings(): void {
  aiSettingsOpen.value = false
}

// ---------------------------------------------------------------------------
// 导入向导（用户示例集合：示例库与应用解耦）
// ---------------------------------------------------------------------------
export const importWizardOpen = ref(false)

export function openImportWizard(): void {
  importWizardOpen.value = true
}
export function closeImportWizard(): void {
  importWizardOpen.value = false
}

/** 删除用户集合示例（sidecar 侧二次校验归属）：成功后关闭详情并刷新列表 */
export async function deleteUserExample(id: string): Promise<boolean> {
  try {
    await api.deleteExample(id)
    selectedId.value = null
    await loadAll()
    pushToast('success', '示例已从你的集合中删除')
    return true
  } catch (err) {
    pushToast('error', `删除失败: ${(err as Error).message}`)
    return false
  }
}

export function setAIStatus(text: string, isError = false): void {
  aiStatus.value = text
  aiStatusError.value = isError
}

export function openAIPanel(): void {
  // 关闭旧面板（如有进行中的解释则一并终止）
  closeAIPanel()
  aiPanelOpen.value = true
  aiOutputText.value = ''
  setAIStatus('正在准备…')
}

export function closeAIPanel(): void {
  // 关闭面板即终止解释：否则流式请求继续消耗 token，结果也无处展示
  if (aiRunId.value) {
    void api.aiStop(aiRunId.value).catch(() => {})
    aiRunId.value = ''
  }
  aiPanelOpen.value = false
}

export function stopAI(): void {
  if (!aiRunId.value) return
  void api.aiStop(aiRunId.value).catch(() => {})
  setAIStatus('已停止')
  aiShowStop.value = false
}

export async function explainSelectedCode(): Promise<void> {
  // 上下文守卫：AI 解释依赖详情页 Monaco 中的代码
  if (!selectedId.value) {
    pushToast('info', '请先在画廊或工具箱打开示例详情，再使用 AI 解释')
    return
  }
  // 防重入：流式解释进行中忽略重复点击
  if (aiRunId.value) return
  // 无 key → 引导设置
  if (!aiSettings.hasKey) {
    openAISettings()
    return
  }
  // 首次使用外发告知
  if (!aiSettings.acknowledged) {
    const ok = window.confirm(
      `代码解释功能会将选中的代码发送到 DeepSeek 服务器（${aiSettings.baseUrl}）进行处理。是否继续？`
    )
    if (!ok) return
    aiSettings.acknowledged = true
    void api.aiSetSettings({ acknowledged: true })
  }

  const code = _editor?.getSelectedText?.() || _editor?.getValue() || ''
  if (!code.trim()) {
    // 先建面板再提示：状态行依赖面板节点存在
    openAIPanel()
    setAIStatus('没有可解释的代码', true)
    return
  }
  const fileName = selectedExample.value?.name || 'example.py'

  openAIPanel()
  setAIStatus('正在请求 DeepSeek…')
  try {
    const res = (await api.aiExplain(code, fileName)) as { status?: string; error?: string; run_id?: string }
    if (res.status === 'error' || res.error) {
      const err = res.error || 'unknown'
      if (err === 'no_api_key') {
        aiSettings.hasKey = false
        setAIStatus('API Key 未配置，请先在设置中填写', true)
      } else {
        setAIStatus('请求失败：' + err, true)
      }
      return
    }
    aiRunId.value = res.run_id || ''
    setAIStatus('正在生成解释…')
    aiShowStop.value = true
  } catch (err) {
    setAIStatus('调用失败：' + (err as Error).message, true)
    aiShowStop.value = false
  }
}

export function initAIEvents(): void {
  api.on('aiExplainChunk', (data) => {
    if (data.run_id && aiRunId.value && data.run_id !== aiRunId.value) return
    aiOutputText.value += data.text || ''
  })
  api.on('aiExplainDone', (data) => {
    if (data.run_id && aiRunId.value && data.run_id !== aiRunId.value) return
    const tokens = data.tokens ? `（约 ${data.tokens} tokens）` : ''
    setAIStatus('完成' + tokens)
    aiRunId.value = ''
    aiShowStop.value = false
  })
  api.on('aiExplainError', (data) => {
    if (data.run_id && aiRunId.value && data.run_id !== aiRunId.value) return
    setAIStatus('生成失败：' + (data.error || 'unknown'), true)
    aiRunId.value = ''
    aiShowStop.value = false
  })
}

export async function copyAIOutput(): Promise<void> {
  if (!aiOutputText.value) return
  try {
    await navigator.clipboard.writeText(aiOutputText.value)
    setAIStatus('已复制到剪贴板')
  } catch {
    setAIStatus('复制失败', true)
  }
}
