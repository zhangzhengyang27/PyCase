// catalog.ts：示例目录域（画廊 / 工具箱的浏览与筛选）。
//
// 职责：示例列表加载、视图与筛选状态、派生列表（筛选/排序/分页/facet/标签计数）、
// 浏览态芯片与侧栏分区范围。持久化数据（收藏/历史/偏好）在 prefs.ts。
import { computed, ref, watch } from 'vue'
import * as FilterEngine from '../filter-engine'
import { THEMES } from '../themes'
import { SECTION_CATALOG, assignSections, sectionKeyOf } from '../overview'
import { buildFilterChips, type FilterChip } from '../filter-chips'
import { interactiveToolItems } from '../interactive-tools'
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

// 画廊分区范围（侧栏二级菜单：'全部示例' = null；否则为一个分区 key）。
// 不持久化——每次打开应用都从「全部示例」起步；会话内随侧栏点击切换。
export const activeSectionKey = ref<string | null>(null)

// 画廊筛选维度
export const activeTheme = ref('all')
export const minQuality = ref(0)
export const sortBy = ref<SortBy>('quality_desc')
export const galleryLimit = ref(120)

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
// 谓词只读 theme_key（判定在服务端），因此按引擎侧的 ExampleLike 收窄类型——
// 原先 cast 成 (e: ExampleItem) 需要调用方再 cast 回 any，等于把类型检查关掉
const THEME_MATCHERS: Record<string, (e: FilterEngine.ExampleLike) => boolean> = Object.fromEntries(
  THEMES.map((t) => [t.key, t.filter as (e: FilterEngine.ExampleLike) => boolean])
)

// ---------------------------------------------------------------------------
// 筛选上下文与查询（computed：依赖变化自动重建，无需手动刷新索引）
// ---------------------------------------------------------------------------
const runStatusIndex = computed(() => FilterEngine.buildRunStatusIndex(runHistory.value))
const lastRunIndex = computed(() => FilterEngine.buildLastRunIndex(runHistory.value))

// 分区筛选判定：sectionKeyOf 对「未命中任何主题/项目/标签组」的条目返回 undefined
// （卡片据此回退分类图标），但这些条目正是 assignSections 的 others 桶——筛选侧需补成
// 'others'，侧栏 15 个分区（含「其他示例」）才能在 sections 维度统一表达。
const sectionKeyForFilter = (ex: FilterEngine.ExampleLike): string | undefined =>
  sectionKeyOf(ex as ExampleItem) ?? 'others'

const filterContext = computed<FilterEngine.FilterContext>(() => ({
  favorites: favorites.value,
  runStatus: runStatusIndex.value,
  themeMatchers: THEME_MATCHERS,
  lastRunAt: lastRunIndex.value,
  codeHitIds: codeHitIds.value,
  // 分区判定单一来源：overview.sectionKeyOf（与 assignSections 同序的 first-match）
  sectionKeyOf: sectionKeyForFilter
}))

const galleryQuery = computed<FilterEngine.FilterQuery>(() => ({
  favOnly: favOnly.value,
  runStatus: activeRunStatus.value,
  runnable: activeRunnable.value,
  theme: activeTheme.value,
  minQuality: minQuality.value,
  tags: Array.from(activeTags.value),
  // 分区范围 = 侧栏二级菜单选中项（null → 全部示例，空数组即不筛）
  sections: activeSectionKey.value ? [activeSectionKey.value] : [],
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
 *  分区范围（sections）同 theme 一样剥离——侧栏 facet 计数不随分区范围缩放 */
const countBaseQuery = computed<FilterEngine.FilterQuery>(() => ({
  ...galleryQuery.value,
  tags: [],
  sections: [],
  theme: 'all',
  minQuality: 0
}))

// ---------------------------------------------------------------------------
// 派生数据（旧版 renderGalleryGrid / renderToolboxGrid / renderFacets 的数据部分）
// ---------------------------------------------------------------------------
/** 画廊池：工具只待在工具箱——画廊（侧栏分区/浏览筛选/侧栏 facet）一律不含 tools，
 *  与工具箱查询的 category:'tools' 互为补集 */
export const galleryExamples = computed<VExample[]>(() => examples.value.filter((e) => e.category !== 'tools'))

/** 画廊分区（互斥分配，质量降序）：侧栏菜单计数与卡片徽章同口径 */
export const gallerySections = computed(() => assignSections(galleryExamples.value))

export interface GallerySectionNav {
  key: string
  label: string
  count: number
}

/** 侧栏二级分区菜单的数据：完整 15 项（SECTION_CATALOG 恒含空分区，计数为 0 也展示），
 *  计数取互斥分配后的成员数（与卡片徽章 / 结果条一致） */
export const gallerySectionNav = computed<GallerySectionNav[]>(() => {
  const counts = new Map(gallerySections.value.map((s) => [s.key, s.items.length]))
  return SECTION_CATALOG.map((s) => ({ key: s.key, label: s.label, count: counts.get(s.key) || 0 }))
})

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

export const filtered = computed(
  () => FilterEngine.filterExamples(galleryExamples.value, galleryQuery.value, filterContext.value) as VExample[]
)

export const sortedGallery = computed(
  () => FilterEngine.sortExamples(filtered.value, sortBy.value, { lastRunAt: lastRunIndex.value }) as VExample[]
)

export const shownGallery = computed(() => sortedGallery.value.slice(0, galleryLimit.value))

export const toolboxItems = computed<VExample[]>(() => {
  const list = FilterEngine.filterExamples(examples.value, toolboxQuery.value, filterContext.value) as VExample[]
  // 交互工具不在 examples 目录池，不走 FilterEngine：客户端匹配搜索词与收藏，恒置顶。
  // 搜索词用 debounce 后的 appliedToolSearch，与目录池口径一致。
  const q = appliedToolSearch.value.trim().toLowerCase()
  const inter = interactiveToolItems.value.filter((t) => {
    if (favOnly.value && !favorites.value.has(t.id)) return false
    if (q && !`${t.name} ${t.title ?? ''} ${t.description ?? ''} ${(t.tags ?? []).join(' ')}`.toLowerCase().includes(q))
      return false
    return true
  })
  return [...inter, ...list]
})

/** 目录池内工具数：可运行率的分母口径（交互工具无 .py 文件，不计入） */
export const catalogToolsTotal = computed(() => examples.value.filter((e) => e.category === 'tools').length)

/** 工具总数：状态栏 / 导航徽章口径（目录池 + 交互工具） */
export const toolsTotal = computed(() => interactiveToolItems.value.length + catalogToolsTotal.value)

/** 视图内排序助手：工具箱分组、画廊等共用同一排序偏好（含最近运行索引） */
export function sortVExamples(list: VExample[]): VExample[] {
  return FilterEngine.sortExamples(list, sortBy.value, { lastRunAt: lastRunIndex.value }) as VExample[]
}

export interface FacetCounts {
  themeCounts: Map<string, number>
  qualityCounts: Map<number, number>
  runnableCounts: Map<string, number>
  /** 运行状态档位计数（成功过 / 失败过 / 未运行）——供工具栏「运行状态」下拉显示 facet 计数 */
  runStatusCounts: Map<string, number>
}

const QUALITY_FACETS = [0, 90, 80, 60]
const RUNNABLE_FACET_KEYS = ['runnable', 'missing_deps', 'empty', 'broken', 'risky']
// 运行状态档位：runStatusIndex 只记 ok/failed，无记录即「未运行」
const RUN_STATUS_FACET_KEYS = ['ok', 'failed', 'never'] as const

export const facetCounts = computed<FacetCounts>(() => {
  const themeCounts = new Map<string, number>()
  const qualityCounts = new Map<number, number>()
  const runnableCounts = new Map<string, number>()
  const runStatusCounts = new Map<string, number>()
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
    for (const key of RUN_STATUS_FACET_KEYS) {
      if (((ctx.runStatus && ctx.runStatus.get(ex.id)) || 'never') === key) {
        runStatusCounts.set(key, (runStatusCounts.get(key) || 0) + 1)
      }
    }
  }
  return { themeCounts, qualityCounts, runnableCounts, runStatusCounts }
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

/** 清空全部筛选（含收藏开关与两个搜索框）。「清空」不清分区：分区是导航语境
 *  （侧栏/页头已表达），退出分区走侧栏「全部示例」或页头「浏览全部」 */
export function clearAllFilters(): void {
  clearFilters()
  favOnly.value = false
  searchQuery.value = ''
  toolSearchQuery.value = ''
}

/** 侧栏二级菜单选取分区范围：null = 全部示例。
 *  分区是「范围」而非叠加筛选——切换范围时清掉主题 facet，避免分区主题与主题维度叠出空集
 *  （15 个分区含 others 统一走 sections 维度，故不再需要 theme/tagsAny/category 三套下钻） */
export function selectSection(key: string | null): void {
  activeSectionKey.value = key
  if (key !== null && activeTheme.value !== 'all') {
    activeTheme.value = 'all'
    persistViewPrefs()
  }
}

/** 页头入口：范围归零（全部示例），可选叠加「我的收藏」开关 */
export function openGallery(preset?: { favOnly?: boolean }): void {
  selectSection(null)
  if (preset?.favOnly) favOnly.value = true
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
      activeSectionKey.value = null
      activeTheme.value = 'all'
      minQuality.value = 0
      activeRunnable.value = 'all'
      activeRunStatus.value = 'all'
      activeTags.value = new Set()
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
