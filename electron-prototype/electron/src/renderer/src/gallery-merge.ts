// gallery-merge.ts：画廊变体归并层（用户语义「变体合并后画廊数量应该少很多」）。
// 规则：凡已路由到实验室/交互页的变体家族（viz/topics 两张表命中的），画廊里折叠为
// 一张家族卡——标题用实验室类型名、带 variantCount、点击照常经 openDetail 路由进
// 交互页（类型/模式预选不受影响）。CLI 工具（标题表命中）、未路由家族（游戏等）、
// 独立单例不折叠。归并发生在筛选之后：搜索「双峰」仍能命中柱状图家族卡。
import { getToolSchema } from './interactive-tools'
import { VIZ_TYPES } from './tool-schemas-viz2'
import { PIL_FAMILIES } from './tool-schemas-pil'
import { CV_OPS } from './tool-schemas-opencv'
import { TURTLE_SHAPES } from './tool-schemas-turtle'
import {
  TITLE_TO_INTERACTIVE,
  TOPICS_FAMILY_TO_INTERACTIVE,
  VIZ_FAMILY_TO_INTERACTIVE,
  topicsFamilyOf,
  vizVariantOf
} from './interactive-mapping'
import type { VExample } from './store/catalog'

interface RegistryLike {
  value: string
  label: string
}

const LAB_REGISTRIES: Record<string, RegistryLike[]> = {
  'interactive:viz-lab': VIZ_TYPES,
  'interactive:pil-lab': PIL_FAMILIES,
  'interactive:cv-lab': CV_OPS,
  'interactive:turtle-lab': TURTLE_SHAPES
}

/** 实验室类型名 > 交互页标题 > 原样家族键 */
function familyLabelOf(page: string, type: string | undefined): string | null {
  const registry = LAB_REGISTRIES[page]
  if (registry) {
    const hit = registry.find((t) => t.value === type) ?? registry[0]
    return hit?.label ?? null
  }
  return getToolSchema(page)?.title ?? null
}

/** 家族折叠元数据：可折叠返回 key + 展示名；不可折叠（CLI 工具/未路由家族/杂项）返回 null */
function familyMetaOf(ex: VExample): { key: string; label: string } | null {
  const title = (ex.title || ex.name || '').replace(/\.py$/i, '').trim()
  if (TITLE_TO_INTERACTIVE[title]) return null // 独立 CLI 工具，一一对应不折叠
  const variant = vizVariantOf(ex)
  if (variant) {
    const route = VIZ_FAMILY_TO_INTERACTIVE[variant.family]
    if (!route) return null
    return { key: `viz:${variant.family}`, label: familyLabelOf(route.page, route.type) ?? variant.family }
  }
  const fam = topicsFamilyOf(ex)
  if (!fam) return null
  const route = TOPICS_FAMILY_TO_INTERACTIVE[fam.family]
  if (!route) return null
  return { key: fam.family, label: familyLabelOf(route.page, route.type) ?? fam.family }
}

/** 变体序号排序键：无尾缀的 base 单例最小（它是变体们的「母本」） */
function variantRankOf(ex: VExample): number {
  const m = /-(?:[vsxd])(\d+)$/.exec(ex.id)
  return m ? Number(m[1]) : 0
}

/**
 * 折叠已路由家族为单卡：代表卡 = 序号最小的变体（母本优先），标题换成家族名，
 * variantCount 标记归并数量。家族卡占该族**首个成员**的位置（与后续排序解耦）。
 * 非家族条目原样通过——可对已折叠池重复调用（幂等）。
 */
export function mergeVariantCards(list: VExample[]): VExample[] {
  // 第一遍：统计各族数量并选代表（母本/最小序号）
  const metaByKey = new Map<string, string>()
  const groups = new Map<string, { count: number; rep: VExample; rank: number }>()
  for (const ex of list) {
    if (ex.variantCount) continue // 已是家族卡：统计阶段跳过（第二循环透传）
    const meta = familyMetaOf(ex)
    if (!meta) continue
    metaByKey.set(ex.id, meta.key)
    const rank = variantRankOf(ex)
    const cur = groups.get(meta.key)
    if (!cur) {
      groups.set(meta.key, { count: 1, rep: ex, rank })
    } else {
      cur.count += 1
      if (rank < cur.rank) {
        cur.rep = ex
        cur.rank = rank
      }
    }
  }
  // 第二遍：首个成员位置输出家族卡，其余成员丢弃，非家族原样通过
  const emitted = new Set<string>()
  const out: VExample[] = []
  for (const ex of list) {
    if (ex.variantCount) {
      out.push(ex) // 已是家族卡：透传，保证对已折叠池重复调用幂等
      continue
    }
    const key = metaByKey.get(ex.id)
    if (!key) {
      out.push(ex)
      continue
    }
    if (emitted.has(key)) continue
    emitted.add(key)
    const g = groups.get(key)!
    const label = familyMetaOf(g.rep)!.label
    if (g.count === 1) {
      // 单例家族：标题统一为类型名（母本即家族卡），不加归并标记
      out.push({ ...g.rep, title: label })
      continue
    }
    out.push({
      ...g.rep,
      title: label,
      variantCount: g.count,
      description: `${g.count} 个变体已归并 · 点卡片打开交互页面，原变体源码可从页内回链查看`
    })
  }
  return out
}
