// 注册表与工具池合并：交互工具恒置顶、参与收藏过滤；不计入可运行率分母口径。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { catalogToolsTotal, examples, favOnly, toolboxItems, toolsTotal, toolSearchQuery } from '../store/catalog'
import { DATE_CALC_ID, interactiveToolItems, isInteractiveId } from '../interactive-tools'
import { favorites } from '../store/prefs'

function seedTools(): void {
  examples.value = [
    {
      id: 'tools_x1',
      name: 'x1.py',
      category: 'tools',
      path: 'tools/x1.py',
      run_status: 'runnable',
      quality_score: 80
    },
    {
      id: 'tools_x2',
      name: 'x2.py',
      category: 'tools',
      path: 'tools/x2.py',
      run_status: 'broken'
    }
  ]
}

beforeEach(() => {
  seedTools()
  favOnly.value = false
  favorites.value = new Set()
})

describe('toolboxItems 合并交互工具', () => {
  it('交互工具置顶且目录池照旧', () => {
    expect(toolboxItems.value[0]?.id).toBe(DATE_CALC_ID)
    expect(toolboxItems.value.map((t) => t.id)).toContain('tools_x1')
  })
  it('收藏过滤作用于交互工具', () => {
    favOnly.value = true
    expect(toolboxItems.value).toHaveLength(0)
    favorites.value = new Set([DATE_CALC_ID])
    expect(toolboxItems.value.map((t) => t.id)).toEqual([DATE_CALC_ID])
  })
  it('toolsTotal 含交互工具，catalogToolsTotal 不含', () => {
    expect(catalogToolsTotal.value).toBe(2)
    expect(toolsTotal.value).toBe(3)
  })
  it('isInteractiveId 前缀判定', () => {
    expect(isInteractiveId(DATE_CALC_ID)).toBe(true)
    expect(isInteractiveId('topics_x')).toBe(false)
    expect(isInteractiveId(undefined)).toBe(false)
  })
  it('注册表条目不含 run_status（不进可运行域）', () => {
    expect(interactiveToolItems.every((t) => t.run_status === undefined)).toBe(true)
  })
  it('搜索词命中交互工具（name 口径，debounce 后生效）', async () => {
    // appliedToolSearch 是模块私有 ref，由 toolSearchQuery 的 watch 防抖 120ms 写入；
    // 与 browse.spec 同一推法：fake timers 推进防抖窗口，再断言合并池仍含交互工具。
    // 'date' 只存在于 name 'date-calculator'（title/description/tags 均中文），专测 name 口径。
    vi.useFakeTimers()
    toolSearchQuery.value = 'date'
    await nextTick()
    vi.advanceTimersByTime(120)
    await nextTick()
    vi.useRealTimers()
    expect(toolboxItems.value.map((t) => t.id)).toContain(DATE_CALC_ID)
  })
})
