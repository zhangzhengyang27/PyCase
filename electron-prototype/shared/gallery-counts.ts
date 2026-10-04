// gallery-counts.ts：画廊池主题计数的运行时派生（smoke 走查用；纯函数便于测试）。
//
// 为什么存在：smoke 曾手写 FROZEN_THEMES 冻结基线（5 主题 × 条数），语料每次增删
// 都要人工同步走查数字——2026-10-04 语料 1496→395 大转向时正是这处钉点把 CI 打红。
// 现在期望值改为运行时从 facts.json（单一真相，与 sidecar 同源）经 TS 侧独立推导，
// 与 Python 侧形成双实现互查：计数漂移必然暴露，但不再需要人工同步；
// 唯一保留的手写物是主题键→分区名的语义胶水表，主题改名/新增时走查会点名。
export interface FactsItem {
  theme?: string | null
  [key: string]: unknown
}

/** 主题键 → 侧栏分区名。仅当 facts 出现新主题/改名时才需要动这里（走查会点名缺哪个）。 */
export const THEME_SECTION_LABELS: Record<string, string> = {
  viz: '数据可视化',
  images: 'PIL 图像处理',
  opencv: 'OpenCV 视觉',
  turtle: 'Turtle 绘图',
  games: 'Pygame 游戏'
}

/** 画廊池 = id 不带 tools_ 前缀的条目（工具箱卡不进示例分区） */
export function isGalleryItem(id: string): boolean {
  return !id.startsWith('tools_')
}

/**
 * 从 facts.items 推导画廊池的主题计数。
 * 返回 unmappedThemes 是刻意的棘轮：facts 冒出新主题而语义表未跟时，
 * 调用方必须显式失败，而不是静默漏检该分区的漂移。
 */
export function deriveGalleryThemeCounts(items: Record<string, FactsItem>): {
  counts: Record<string, number>
  poolTotal: number
  unmappedThemes: string[]
} {
  const counts: Record<string, number> = {}
  const seen = new Set<string>()
  let poolTotal = 0
  for (const [id, item] of Object.entries(items)) {
    if (!isGalleryItem(id)) continue
    poolTotal += 1
    const theme = item.theme ?? null
    if (theme === null) continue
    seen.add(theme)
    counts[theme] = (counts[theme] ?? 0) + 1
  }
  const unmappedThemes = [...seen].filter((t) => !(t in THEME_SECTION_LABELS))
  return { counts, poolTotal, unmappedThemes }
}
