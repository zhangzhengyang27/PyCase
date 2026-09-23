// filter-chips.ts：结果条筛选芯片的纯函数构建（无 DOM / store 依赖）
// 从 FilterQuery 快照生成可逐个移除的芯片列表，让「当前生效了哪些筛选」
// 不必到侧栏 36 行里找高亮。标签映射导出供 BrowseToolbar 与测试共用。
import { THEMES } from './themes'
import { tagSectionLabel, PROJECTS_SECTION_META } from './overview'
import type { FilterQuery } from './filter-engine'

export type ChipKey = 'fav' | 'runStatus' | 'runnable' | 'theme' | 'quality' | 'tag' | 'tagsAny' | 'category' | 'q'

export interface FilterChip {
  key: ChipKey
  /** 同 key 多芯片时的身份（tag 的标签名 / quality 下限），单值芯片为 '1' */
  value: string
  label: string
}

export const RUN_STATUS_LABELS: Record<string, string> = {
  ok: '成功过',
  failed: '失败过',
  never: '未运行'
}

export const RUNNABLE_LABELS: Record<string, string> = {
  runnable: '可运行',
  missing_deps: '缺依赖',
  empty: '空壳',
  broken: '语法损坏',
  risky: '高危'
}

export function buildFilterChips(q: FilterQuery): FilterChip[] {
  const chips: FilterChip[] = []
  if (q.favOnly) chips.push({ key: 'fav', value: '1', label: '我的收藏' })
  if (q.runStatus && q.runStatus !== 'all') {
    chips.push({ key: 'runStatus', value: q.runStatus, label: RUN_STATUS_LABELS[q.runStatus] || q.runStatus })
  }
  if (q.runnable && q.runnable !== 'all') {
    chips.push({ key: 'runnable', value: q.runnable, label: RUNNABLE_LABELS[q.runnable] || q.runnable })
  }
  if (q.theme && q.theme !== 'all') {
    const t = THEMES.find((x) => x.key === q.theme)
    chips.push({ key: 'theme', value: q.theme, label: t ? t.label : q.theme })
  }
  if (q.minQuality && q.minQuality > 0) {
    chips.push({ key: 'quality', value: String(q.minQuality), label: `质量分 ≥${q.minQuality}` })
  }
  for (const tag of q.tags || []) {
    chips.push({ key: 'tag', value: tag, label: `#${tag}` })
  }
  const kw = (q.q || '').trim()
  if (kw) chips.push({ key: 'q', value: kw, label: `搜索：${kw}` })
  return chips
}
