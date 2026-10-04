// overview.ts：画廊总览态的分区分配（纯函数，无 DOM / store 依赖）
// 分区 = 主题 first-match 互斥分配（一张卡只出现在一个分区，预览不重复）；
// 未命中主题的条目再按标签组分配，剩余进其他桶。
// 区头计数即 members 长度（互斥口径，与预览成员一致）。
import { THEMES } from './themes'
import type { ExampleItem } from './types'

export interface OverviewSection {
  key: string
  label: string
  /** 互斥分配后的全部成员，已按质量分降序（同分按 id 稳定排序），预览取前 N */
  items: ExampleItem[]
  /** 下钻方式：theme=设主题筛选；tags=设分区标签组（OR）；projects=按类目；others=仅进入浏览态 */
  kind: 'theme' | 'tags' | 'projects' | 'others'
  /** kind='tags' 时的标签组（下钻传给 tagsAny） */
  tags?: string[]
}

/** 其他桶元数据（空则省略该分区） */
const OTHERS_META = { key: 'others', label: '其他示例' } as const

/**
 * 标签分区表：把五大主题未覆盖的长尾示例（原「其他示例」大头）按语义标签组再分类。
 * 命中 = 条目元数据标签与组内任一标签相交；数组顺序即分区展示与分配优先级。
 * 标签清单刻意避开 import 自动标签（如裸 requests），保证分区计数与下钻结果一致。
 */
export const TAG_SECTIONS: ReadonlyArray<{ key: string; label: string; tags: string[] }> = [
  {
    key: 'tag:basics',
    label: '语言基础',
    tags: [
      'python-basics',
      'language-fundamentals',
      'python-core-concepts',
      'data-types',
      'python-modules-files-functions',
      '基础'
    ]
  },
  {
    key: 'tag:algo',
    label: '算法与数据结构',
    tags: ['algorithms', 'algorithm', '数据结构', '排序', '算法']
  },
  {
    key: 'tag:crawler',
    label: '网络爬虫',
    tags: ['爬虫', '网络爬虫']
  },
  {
    key: 'tag:data',
    label: '数据分析',
    tags: ['数据分析']
  },
  {
    key: 'tag:db',
    label: '数据库',
    tags: ['数据库', 'sqlite']
  },
  {
    key: 'tag:web',
    label: 'Web 开发',
    tags: ['Web开发', 'web']
  },
  {
    key: 'tag:async',
    label: '并发与异步',
    tags: ['并发', 'asyncio']
  }
]

/**
 * 侧栏二级分区菜单的完整元数据表（与 assignSections 完全同序：
 * 5 主题 → 7 标签组 → 其他 = 13 项）。
 * 与 assignSections 的唯一差别：others 恒在（菜单需完整 8 项，计数为 0 也展示），
 * 而 assignSections 会在 others 为空时省略该分区以避开「0 个」噪音。
 * 分区下钻统一走「分区」筛选维度（FilterQuery.sections），故此处不再需要 kind 驱动下钻分支。
 */
export interface SectionMeta {
  key: string
  label: string
  kind: 'theme' | 'tags' | 'projects' | 'others'
  tags?: string[]
}

export const SECTION_CATALOG: readonly SectionMeta[] = [
  ...THEMES.map((t) => ({ key: t.key, label: t.label, kind: 'theme' as const })),
  ...TAG_SECTIONS.map((s) => ({ key: s.key, label: s.label, kind: 'tags' as const, tags: s.tags })),
  { ...OTHERS_META, kind: 'others' as const }
]

/** 分区 key → 展示名（侧栏菜单 / 结果条范围标题 / 筛选芯片共用）；未命中返回 undefined */
export function sectionLabelOf(key: string | null | undefined): string | undefined {
  return key ? SECTION_CATALOG.find((s) => s.key === key)?.label : undefined
}

/** 卡片视觉元数据解析：与 assignSections 完全同序的 first-match——
    主题 → 综合项目 → 标签组；未命中（others/未知分类）返回 undefined，消费方回退分类图标。
    WeakMap 备忘：filter 谓词会对 code 跑正则，逐卡渲染时不重复计算。 */
const sectionKeyMemo = new WeakMap<object, string | undefined>()

export function sectionKeyOf(ex: ExampleItem): string | undefined {
  if (sectionKeyMemo.has(ex)) return sectionKeyMemo.get(ex)
  const theme = THEMES.find((t) => t.filter(ex))
  let key: string | undefined
  if (theme) key = theme.key
  else {
    const tagHit = TAG_SECTIONS.find((spec) => (ex.tags || []).some((t) => spec.tags.includes(t)))
    key = tagHit?.key
  }
  sectionKeyMemo.set(ex, key)
  return key
}

/** 保存编辑后调用：ex.code 原地变更使分区判定失效，清除备忘让徽章随分区重算 */
export function invalidateExampleVisual(ex: ExampleItem): void {
  sectionKeyMemo.delete(ex)
}

/** 按标签组反查分区名（结果条范围标题用）；未命中返回 undefined */
export function tagSectionLabel(tags: readonly string[]): string | undefined {
  const set = new Set(tags.map((t) => String(t).toLowerCase()))
  return TAG_SECTIONS.find((spec) => spec.tags.some((t) => set.has(t)))?.label
}

function byQuality<T extends ExampleItem>(a: T, b: T): number {
  return (b.quality_score ?? 0) - (a.quality_score ?? 0) || a.id.localeCompare(b.id)
}

export function assignSections<T extends ExampleItem>(examples: readonly T[]): OverviewSection[] {
  const themeBuckets = new Map<string, T[]>(THEMES.map((t) => [t.key, []]))
  const tagBuckets = new Map<string, T[]>(TAG_SECTIONS.map((s) => [s.key, []]))
  const others: T[] = []
  for (const ex of examples) {
    const theme = THEMES.find((t) => t.filter(ex))
    if (theme) {
      themeBuckets.get(theme.key)!.push(ex)
      continue
    }
    const tagHit = TAG_SECTIONS.find((spec) => (ex.tags || []).some((t) => spec.tags.includes(t)))
    if (tagHit) {
      tagBuckets.get(tagHit.key)!.push(ex)
      continue
    }
    others.push(ex)
  }
  const sections: OverviewSection[] = [
    ...THEMES.map((t) => ({
      key: t.key,
      label: t.label,
      items: (themeBuckets.get(t.key) || []).slice().sort(byQuality),
      kind: 'theme' as const
    })),
    ...TAG_SECTIONS.map((s) => ({
      key: s.key,
      label: s.label,
      items: (tagBuckets.get(s.key) || []).slice().sort(byQuality),
      kind: 'tags' as const,
      tags: s.tags
    }))
  ]
  // 其他桶为空时省略，避免「0 个」的噪音分区
  if (others.length > 0)
    sections.push({ ...OTHERS_META, items: others.slice().sort(byQuality), kind: 'others' as const })
  return sections
}
