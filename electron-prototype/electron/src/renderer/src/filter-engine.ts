// filter-engine.ts：多维筛选纯函数引擎（无 DOM、无全局状态依赖）
// 维度：分类 category × 收藏 favorites × 运行状态 runStatus × 标签 tags × 全文 q

// 常见标准库/内置模块：不自动作为标签（避免 os/sys 之类淹没第三方库标签）
const STDLIB = new Set([
  'abc', 'argparse', 'ast', 'asyncio', 'base64', 'bisect', 'calendar', 'collections',
  'concurrent', 'configparser', 'contextlib', 'copy', 'csv', 'ctypes', 'dataclasses',
  'datetime', 'decimal', 'difflib', 'email', 'enum', 'fnmatch', 'functools', 'glob',
  'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'importlib', 'inspect', 'io',
  'itertools', 'json', 'logging', 'math', 'multiprocessing', 'operator', 'os', 'pathlib',
  'pickle', 'pprint', 'queue', 'random', 're', 'shutil', 'signal', 'socket', 'sqlite3',
  'statistics', 'string', 'struct', 'subprocess', 'sys', 'tempfile', 'textwrap',
  'threading', 'time', 'traceback', 'types', 'typing', 'unittest', 'urllib', 'uuid',
  'warnings', 'weakref', 'xml', 'zipfile'
])

const IMPORT_RE = /^\s*(?:from|import)\s+([\w.]+)/gm

export interface ExampleLike {
  id: string
  name: string
  category: string
  code?: string
  tags?: string[]
  _importTags?: string[]
  /** 派生事实：命中主题（服务端下发；列表不含 code，判定不在前端） */
  theme_key?: string | null
  quality_score?: number
  /** 可运行性派生状态（sidecar run_status 字段） */
  run_status?: string
  /** 预处理缓存：code 的小写形式（loadExamples 一次性构建，搜索热路径免重复 toLowerCase） */
  _codeLower?: string
  /** 预处理缓存：全部标签（元数据 + import 自动标签，loadExamples 一次性构建） */
  _tagsAll?: string[]
}

/** 可运行性筛选维度：all = 不筛 */
export type RunnableFilter = 'all' | 'runnable' | 'missing_deps' | 'empty' | 'broken' | 'risky'

export interface FilterQuery {
  category?: string
  favOnly?: boolean
  runStatus?: 'all' | 'ok' | 'failed' | 'never'
  runnable?: RunnableFilter
  tags?: string[]
  /** 标签任一命中（OR）：总览分区下钻用——一个分区对应一组同义标签 */
  tagsAny?: string[]
  q?: string
  /** 主题维度（画廊筛选条）：'all' 或主题 key，匹配器由 ctx.themeMatchers 提供 */
  theme?: string
  /** 质量分下限（0-100，0 = 不筛） */
  minQuality?: number
}

export interface FilterContext {
  favorites?: Set<string>
  runStatus?: Map<string, string>
  /** 主题 key → 谓词（THEMES[].filter，由调用方注入，保持本模块零业务依赖） */
  themeMatchers?: Record<string, (ex: any) => boolean>
  /** 示例 id → 最近一次运行时间戳 ms（排序用） */
  lastRunAt?: Map<string, number>
  /** 服务端代码检索命中 id（v2 列表不含 code，代码搜索由 sidecar 承接） */
  codeHitIds?: Set<string>
}

export interface TagFacet {
  tag: string
  count: number
}

/**
 * 从源码抽取第三方 import 根模块名作为自动标签（去标准库、去相对导入）。
 */
export function extractImportTags(code: string): string[] {
  if (!code || typeof code !== 'string') return []
  const found = new Set<string>()
  let m: RegExpExecArray | null
  IMPORT_RE.lastIndex = 0
  while ((m = IMPORT_RE.exec(code)) !== null) {
    const mod = m[1]
    if (!mod || mod.startsWith('.')) continue
    const root = mod.split('.')[0].toLowerCase()
    if (!root || STDLIB.has(root)) continue
    found.add(root)
  }
  return Array.from(found).sort()
}

/**
 * 汇总示例的全部标签：元数据 tags + import 自动标签。
 * 命中 _tagsAll 预处理缓存时直接返回（调用方在代码/标签变化后负责重建）。
 */
export function allTagsOf(ex: ExampleLike): string[] {
  if (Array.isArray(ex._tagsAll)) return ex._tagsAll
  const meta = Array.isArray(ex.tags) ? ex.tags.map((t) => String(t).toLowerCase()) : []
  const auto = ex._importTags || extractImportTags(ex.code || '')
  return Array.from(new Set(meta.concat(auto)))
}

/**
 * 由运行历史构建 示例id → 最近一次运行状态 的索引。
 */
export function buildRunStatusIndex(history: Array<{ id: string; ok: boolean; ts: string }>): Map<string, 'ok' | 'failed'> {
  const idx = new Map<string, 'ok' | 'failed'>()
  if (!Array.isArray(history)) return idx
  for (const h of history) {
    if (!h || !h.id || idx.has(h.id)) continue
    idx.set(h.id, h.ok ? 'ok' : 'failed')
  }
  return idx
}

/**
 * 构造查询对象（补齐缺省维度，避免调用方漏字段导致 undefined 比较）。
 */
export function normalizeQuery(query: FilterQuery): Required<FilterQuery> {
  const q = query || {}
  const minQuality = typeof q.minQuality === 'number' && q.minQuality > 0 ? q.minQuality : 0
  return {
    category: typeof q.category === 'string' ? q.category : 'all',
    favOnly: !!q.favOnly,
    runStatus: (['ok', 'failed', 'never'] as const).includes(q.runStatus as 'ok' | 'failed' | 'never') ? (q.runStatus as 'ok' | 'failed' | 'never') : 'all',
    runnable: (['runnable', 'missing_deps', 'empty', 'broken', 'risky'] as readonly string[]).includes(String(q.runnable)) ? (q.runnable as RunnableFilter) : 'all',
    tags: Array.isArray(q.tags) ? q.tags.map((t) => String(t).toLowerCase()) : [],
    tagsAny: Array.isArray(q.tagsAny) ? q.tagsAny.map((t) => String(t).toLowerCase()) : [],
    q: typeof q.q === 'string' ? q.q.toLowerCase().trim() : '',
    theme: typeof q.theme === 'string' && q.theme ? q.theme : 'all',
    minQuality
  }
}

/**
 * 单个示例是否通过全部维度（AND 组合；同一维度内：标签为 AND，其余为单值）。
 */
export function matchExample(ex: ExampleLike, rawQuery: FilterQuery, ctx?: FilterContext): boolean {
  const query = normalizeQuery(rawQuery)
  const favorites = (ctx && ctx.favorites) || new Set<string>()
  const runStatus = (ctx && ctx.runStatus) || new Map<string, string>()

  // 1) 分类
  if (query.category !== 'all' && ex.category !== query.category) return false

  // 2) 主题（谓词由 ctx 注入；all 或无匹配器时跳过）
  if (query.theme !== 'all') {
    const matcher = ctx && ctx.themeMatchers ? ctx.themeMatchers[query.theme] : undefined
    if (matcher && !matcher(ex)) return false
  }

  // 3) 质量分下限
  if (query.minQuality > 0 && (ex.quality_score ?? 0) < query.minQuality) return false

  // 4) 收藏
  if (query.favOnly && !favorites.has(ex.id)) return false

  // 5) 运行状态
  if (query.runStatus !== 'all') {
    const st = runStatus.get(ex.id)
    if (query.runStatus === 'never') {
      if (st) return false
    } else if (st !== query.runStatus) {
      return false
    }
  }

  // 6) 可运行性（sidecar 派生状态；run_status 缺失视为未知，仅匹配 runnable 时放行未知项之外的状态）
  if (query.runnable !== 'all') {
    if (ex.run_status !== query.runnable) return false
  }

  // 7) 标签（多选 AND：每个选中标签都要命中）
  if (query.tags.length > 0) {
    const tags = allTagsOf(ex)
    if (!query.tags.every((t) => tags.includes(t))) return false
  }

  // 7b) 标签任一命中（OR，分区下钻）：命中组内任意标签即放行
  if (query.tagsAny.length > 0) {
    const tags = allTagsOf(ex)
    if (!query.tagsAny.some((t) => tags.includes(t))) return false
  }

  // 8) 全文（名称 / 标签 / 代码）
  if (query.q) {
    const hitName = ex.name && ex.name.toLowerCase().includes(query.q)
    const hitTags = allTagsOf(ex).some((t) => t.includes(query.q))
    // 优先命中 _codeLower 预处理缓存，避免每次按键对 1300+ 示例重新 toLowerCase
    const codeLower = ex._codeLower !== undefined ? ex._codeLower : (ex.code || '').toLowerCase()
    const hitCode = !!codeLower && codeLower.includes(query.q)
    // v2：列表不带 code，代码命中由服务端检索给出（ctx.codeHitIds）
    const hitServer = !!(ctx && ctx.codeHitIds && ctx.codeHitIds.has(ex.id))
    if (!hitName && !hitTags && !hitCode && !hitServer) return false
  }
  return true
}

/** 列表过滤 */
export function filterExamples(list: ExampleLike[], query: FilterQuery, ctx?: FilterContext): ExampleLike[] {
  return (list || []).filter((ex) => matchExample(ex, query, ctx))
}

export type SortBy = 'quality_desc' | 'name' | 'last_run'

/**
 * 排序：质量分降序（默认）/ 名称 / 最近运行。
 * last_run 需 ctx.lastRunAt，未运行的排最后；其余维度按名称升序作稳定次序。
 */
export function sortExamples(list: ExampleLike[], sortBy: SortBy, ctx?: FilterContext): ExampleLike[] {
  const arr = (list || []).slice()
  const byName = (a: ExampleLike, b: ExampleLike) => (a.name || '').localeCompare(b.name || '')
  if (sortBy === 'name') {
    arr.sort(byName)
  } else if (sortBy === 'last_run') {
    const lastRunAt = (ctx && ctx.lastRunAt) || new Map<string, number>()
    arr.sort((a, b) => (lastRunAt.get(b.id) || 0) - (lastRunAt.get(a.id) || 0) || byName(a, b))
  } else {
    arr.sort((a, b) => (b.quality_score ?? 0) - (a.quality_score ?? 0) || byName(a, b))
  }
  return arr
}

/**
 * 由运行历史构建 示例id → 最近一次运行时间戳 ms（历史最新在前，同一示例只取第一条）。
 */
export function buildLastRunIndex(history: Array<{ id: string; ts: string }>): Map<string, number> {
  const idx = new Map<string, number>()
  if (!Array.isArray(history)) return idx
  for (const h of history) {
    if (!h || !h.id || idx.has(h.id)) continue
    const t = Date.parse(h.ts)
    idx.set(h.id, Number.isNaN(t) ? 0 : t)
  }
  return idx
}

/**
 * 构建标签 facet：标签 → 命中示例数（按当前 query 中除标签外的条件统计）。
 */
export function buildTagFacets(list: ExampleLike[], rawQuery: FilterQuery, ctx?: FilterContext, limit?: number): TagFacet[] {
  const query = normalizeQuery(rawQuery)
  const base = { ...query, tags: [] } // 统计标签时不应用已选标签
  const counts = new Map<string, number>()
  ;(list || []).forEach((ex) => {
    if (!matchExample(ex, base, ctx)) return
    new Set(allTagsOf(ex)).forEach((t) => counts.set(t, (counts.get(t) || 0) + 1))
  })
  const arr: TagFacet[] = Array.from(counts, ([tag, count]) => ({ tag, count }))
  arr.sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag))
  return typeof limit === 'number' ? arr.slice(0, limit) : arr
}

export { STDLIB }
