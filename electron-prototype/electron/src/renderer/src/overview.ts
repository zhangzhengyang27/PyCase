// overview.ts：画廊总览态的分区分配（纯函数，无 DOM / store 依赖）
// 分区 = 主题 first-match 互斥分配（一张卡只出现在一个分区，预览不重复）；
// 未命中主题的条目再按「综合项目 → 标签组」依次分配，剩余进其他桶。
// 区头计数即 members 长度（互斥口径，与预览成员一致）。
import { THEMES } from './themes'
import type { ExampleItem } from './types'

export interface OverviewSection {
  key: string
  label: string
  icon: string
  /** 互斥分配后的全部成员，已按质量分降序（同分按 id 稳定排序），预览取前 N */
  items: ExampleItem[]
  /** 下钻方式：theme=设主题筛选；tags=设分区标签组（OR）；projects=按类目；others=仅进入浏览态 */
  kind: 'theme' | 'tags' | 'projects' | 'others'
  /** kind='tags' 时的标签组（下钻传给 tagsAny） */
  tags?: string[]
}

/** 其他桶元数据（空则省略该分区） */
const OTHERS_META = { key: 'others', label: '其他示例', icon: '📦' } as const

/** 综合项目区：主题未覆盖的 projects 条目单列（项目名标签各自为政，标签组收编不了） */
export const PROJECTS_SECTION_META = { key: 'projects', label: '综合项目', icon: '🚀' } as const

/**
 * 标签分区表：把五大主题未覆盖的长尾示例（原「其他示例」大头）按语义标签组再分类。
 * 命中 = 条目元数据标签与组内任一标签相交；数组顺序即分区展示与分配优先级。
 * 标签清单刻意避开 import 自动标签（如裸 requests），保证分区计数与下钻结果一致。
 */
export const TAG_SECTIONS: ReadonlyArray<{ key: string; label: string; icon: string; tags: string[] }> = [
  {
    key: 'tag:basics',
    label: '语言基础',
    icon: '🧱',
    tags: ['python-basics', 'language-fundamentals', 'python-core-concepts', 'data-types', 'python-modules-files-functions', '基础']
  },
  {
    key: 'tag:advanced',
    label: '进阶与并发',
    icon: '⚡',
    tags: ['python-advanced', 'language-advanced', 'python-core-advanced', '并发', '并发编程', 'concurrency']
  },
  {
    key: 'tag:crawling',
    label: '网络爬虫',
    icon: '🕸️',
    tags: ['web-crawling', '网络', 'scrapy-projects', 'http-requests-basics', 'urllib-basics', 'spider-techniques', 'requests-beautifulsoup', '爬虫', 'crawler']
  },
  {
    key: 'tag:webapp',
    label: 'Web 应用',
    icon: '🌐',
    tags: ['web-development', 'Web', 'flask', 'flask-advanced-examples', 'flask-mumunote', 'django', 'fastapi']
  },
  {
    key: 'tag:office',
    label: '办公自动化',
    icon: '📑',
    tags: ['office-automation', 'job-auto', 'jobautopilot-extras', 'productivity-course', '办公']
  },
  {
    key: 'tag:database',
    label: '数据库',
    icon: '🗄️',
    tags: ['databases', '数据库', 'sqlite', 'mysql', 'mongodb', 'redis']
  },
  {
    key: 'tag:testing',
    label: '自动化测试',
    icon: '🧪',
    tags: ['automation-testing', 'pytest', 'unittest', '测试']
  },
  {
    key: 'tag:algo',
    label: '算法与数据结构',
    icon: '🧮',
    tags: ['algorithms', 'algorithm', '数据结构', '排序', '算法']
  }
]

/** 分区色相（specs §3.2）：区头图标徽章经 .hue-chip + 内联 --hue 消费；others 不配色相（中性灰） */
export const SECTION_HUES: Record<string, string> = {
  viz: '#5e6ad2',
  turtle: '#2fa866',
  games: '#9a6bf2',
  opencv: '#3d8fe0',
  images: '#e0566a',
  'tag:basics': '#64748b',
  'tag:advanced': '#d9a03d',
  'tag:crawling': '#e07840',
  'tag:webapp': '#38a8e0',
  'tag:office': '#8a7dd8',
  'tag:database': '#2fb8a6',
  'tag:testing': '#7fb846',
  'tag:algo': '#5f8dd9',
  projects: '#d471a8'
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
  else if (ex.category === 'projects') key = 'projects'
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

/** 分区 key → emoji（主题与标签组的 icon 字段 + 综合项目） */
const SECTION_EMOJI: Record<string, string> = {
  ...Object.fromEntries(THEMES.map((t) => [t.key, t.icon])),
  ...Object.fromEntries(TAG_SECTIONS.map((s) => [s.key, s.icon])),
  projects: PROJECTS_SECTION_META.icon
}

/** 卡片/详情页图标徽章视觉：命中分区返回 emoji+色相，未命中返回 undefined */
export function exampleVisual(ex: ExampleItem): { emoji: string; hue: string } | undefined {
  const key = sectionKeyOf(ex)
  if (!key) return undefined
  const emoji = SECTION_EMOJI[key]
  const hue = SECTION_HUES[key]
  return emoji && hue ? { emoji, hue } : undefined
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
  const projects: T[] = []
  const tagBuckets = new Map<string, T[]>(TAG_SECTIONS.map((s) => [s.key, []]))
  const others: T[] = []
  for (const ex of examples) {
    const theme = THEMES.find((t) => t.filter(ex))
    if (theme) {
      themeBuckets.get(theme.key)!.push(ex)
      continue
    }
    // 项目先于标签组：项目名标签各自为政，且项目是展示型条目，值得独立一区
    if (ex.category === 'projects') {
      projects.push(ex)
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
      icon: t.icon,
      items: (themeBuckets.get(t.key) || []).slice().sort(byQuality),
      kind: 'theme' as const
    })),
    ...TAG_SECTIONS.map((s) => ({
      key: s.key,
      label: s.label,
      icon: s.icon,
      items: (tagBuckets.get(s.key) || []).slice().sort(byQuality),
      kind: 'tags' as const,
      tags: s.tags
    })),
    { ...PROJECTS_SECTION_META, items: projects.slice().sort(byQuality), kind: 'projects' as const }
  ]
  // 其他桶为空时省略，避免「0 个」的噪音分区
  if (others.length > 0) sections.push({ ...OTHERS_META, items: others.slice().sort(byQuality), kind: 'others' as const })
  return sections
}
