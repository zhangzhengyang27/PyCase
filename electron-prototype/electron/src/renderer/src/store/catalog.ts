// catalog.ts：示例目录域（画廊 / 工具箱的浏览与筛选）。
//
// 职责：示例列表加载、视图与筛选状态、派生列表（筛选/排序/分页/facet/标签计数）、
// 浏览态芯片与两级浏览入口。持久化数据（收藏/历史/偏好）在 prefs.ts。
import { computed, ref, watch } from 'vue'
import * as FilterEngine from '../filter-engine'
import { THEMES } from '../themes'
import { buildFilterChips, type FilterChip } from '../filter-chips'
import type { ExampleItem } from '../types'
import { api } from '../sidecar-client'
import { favorites, runHistory, toggleFavorite, recordHistory, toPlain } from './prefs'


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

export const favOnly = ref(false)
export const activeRunStatus = ref<'all' | 'ok' | 'failed' | 'never'>('all')
export const activeRunnable = ref<FilterEngine.RunnableFilter>('all')
export const activeTags = ref(new Set<string>())

// 搜索防抖：输入框即时回显，筛选应用延迟 120ms（旧版 150ms 防抖的等价物，
// 差别在于旧版防的是全量 innerHTML 重建，这里防的是大集合上的谓词扫描）
let _galleryTimer: ReturnType<typeof setTimeout> | undefined
let _toolboxTimer: ReturnType<typeof setTimeout> | undefined
const appliedSearch = ref('')
const appliedToolSearch = ref('')
// 服务端代码检索命中集（契约 §5：列表不含 code，代码搜索由 sidecar 按需读文件）
const codeHitIds = ref<Set<string>>(new Set())
let _hitTimer: ReturnType<typeof setTimeout> | undefined
watch(searchQuery, (v) => {
  clearTimeout(_galleryTimer)
  _galleryTimer = setTimeout(() => (appliedSearch.value = v), 120)
  // 代码命中另拉一次服务端检索（更长防抖，避免逐字符打请求）；短查询不值当
  clearTimeout(_hitTimer)
  if (v.trim().length < 2) {
    codeHitIds.value = new Set()
    return
  }
  _hitTimer = setTimeout(() => void refreshCodeHits(v.trim()), 260)
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
  lastRunAt: lastRunIndex.value,
  codeHitIds: codeHitIds.value
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

/** 服务端代码检索：命中 id 并入筛选（失败时静默降级为仅元数据匹配） */
async function refreshCodeHits(query: string): Promise<void> {
  try {
    const res = (await api.searchExamples(query)) as { hits?: Array<{ id: string; reason: string }> }
    codeHitIds.value = new Set((res?.hits || []).filter((h) => h.reason === 'code').map((h) => h.id))
  } catch (err) {
    console.error('[search] 服务端检索失败，代码搜索降级:', err)
    codeHitIds.value = new Set()
  }
}

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

export function applyViewPrefs(prefs: unknown): void {
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


/** 拉取示例列表并建立筛选预处理缓存（v2：import 标签用服务端下发的派生事实）。 */
export async function loadExamples(): Promise<void> {
  const result = await api.listExamples()
  const list = (result.examples || []) as VExample[]
  for (const ex of list) {
    ex._importTags = Array.isArray(ex.import_tags) ? ex.import_tags : []
    ex._codeLower = ''
    ex._tagsAll = FilterEngine.allTagsOf(ex)
  }
  examples.value = list
}


// ---------------------------------------------------------------------------
// 测试钩子（画廊/工具箱浏览）：由 store/index.ts 的 getTestApi 组合成 window.__app
// ---------------------------------------------------------------------------
export function catalogTestHooks(): Record<string, unknown> {
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
      codeHitIds.value = new Set()
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
    setSearch: (q: string) => {
      searchQuery.value = q
    },
    appliedSearch: () => appliedSearch.value,
    codeHitIds: () => Array.from(codeHitIds.value),
    setSortBy: (s: 'quality_desc' | 'name' | 'last_run') => {
      sortBy.value = s
      persistViewPrefs()
    },
    setTags: (tags: string[]) => {
      activeTags.value = new Set(tags)
    },
    tagFacetsFor: (scope: 'gallery' | 'toolbox') => tagFacetsFor(scope),
    findByName: (name: string) => examples.value.find((e) => e.name === name) || null,
    // 走查脚本用：外部（主进程）导入/user 操作后刷新目录列表
    reload: () => loadExamples()
  }
}
