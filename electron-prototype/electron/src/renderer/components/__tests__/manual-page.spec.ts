// ToolManualPage + 手册路由/入口（W7）。
// 手册数据是模块级 JSON：用真实数据断言覆盖面；页面行为用 mock detail store 钉。
import { beforeEach, describe, expect, it, vi } from 'vitest'

const hoisted = vi.hoisted(() => ({
  runFromCard: vi.fn(),
  openDetail: vi.fn()
}))

vi.mock('../../src/store/detail', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/store/detail')>()
  return { ...actual, runFromCard: hoisted.runFromCard, openDetail: hoisted.openDetail }
})

import { mount } from '@vue/test-utils'
import ToolManualPage from '../interactive/ToolManualPage.vue'
import { manualExampleId, manualFor, hasManual, isManualId, openManual, MANUAL_PREFIX } from '../../src/tool-manuals'
import { selectedId } from '../../src/store/detail'
import manualsJson from '../../src/tool-manuals.json'

beforeEach(() => {
  hoisted.runFromCard.mockClear()
  hoisted.openDetail.mockClear()
  selectedId.value = null
})

describe('手册数据覆盖面（构建期生成器守卫的运行时镜像）', () => {
  const manuals = (manualsJson as { manuals: Record<string, unknown> }).manuals
  it('手册数量 ≥ 100（全部未页化工具的底线）', () => {
    expect(Object.keys(manuals).length).toBeGreaterThanOrEqual(100)
  })
  it('每份手册都有标题/概述/用法', () => {
    for (const [id, m] of Object.entries(manuals)) {
      expect((m as { title: string }).title.trim(), id).toBeTruthy()
      expect((m as { summary: string }).summary.trim(), id).toBeTruthy()
      expect((m as { usage: string }).usage.trim(), id).toBeTruthy()
    }
  })
})

describe('tool-manuals 工具函数', () => {
  it('前缀判定与 id 剥离', () => {
    expect(isManualId('manual:tools_x')).toBe(true)
    expect(isManualId('interactive:x')).toBe(false)
    expect(isManualId(undefined)).toBe(false)
    expect(manualExampleId('manual:tools_x')).toBe('tools_x')
    expect(manualExampleId('tools_x')).toBeNull()
  })
  it('openManual 写 selectedId（容空不炸）', () => {
    openManual('tools_csv-stats')
    expect(selectedId.value).toBe(`${MANUAL_PREFIX}tools_csv-stats`)
    openManual(null)
    openManual(undefined)
  })
  it('hasManual / manualFor 对真实数据生效', () => {
    const firstId = Object.keys((manualsJson as { manuals: Record<string, unknown> }).manuals)[0]!
    expect(hasManual(firstId)).toBe(true)
    expect(manualFor(firstId)).toBeTruthy()
    expect(hasManual('manual:ghost')).toBe(false)
    expect(manualFor('ghost')).toBeUndefined()
  })
})

describe('ToolManualPage', () => {
  const firstId = Object.keys((manualsJson as { manuals: Record<string, unknown> }).manuals)[0]!
  const entry = manualFor(firstId)!

  it('渲染概述/用法/参数表/注意点', () => {
    selectedId.value = `${MANUAL_PREFIX}${firstId}`
    const w = mount(ToolManualPage)
    expect(w.find('[data-testid="manual-summary"]').text()).toBe(entry.summary)
    expect(w.find('[data-testid="manual-usage"]').text()).toBe(entry.usage)
    expect(w.findAll('[data-testid="manual-params"] > div')).toHaveLength(entry.params.length)
  })
  it('运行按钮交接 runFromCard（不自带运行器）', async () => {
    selectedId.value = `${MANUAL_PREFIX}${firstId}`
    const w = mount(ToolManualPage)
    await w.find('[data-testid="manual-run"]').trigger('click')
    expect(hoisted.runFromCard).toHaveBeenCalledWith(firstId)
    await w.find('[data-testid="manual-open-detail"]').trigger('click')
    expect(hoisted.openDetail).toHaveBeenCalledWith(firstId)
  })
  it('返回按钮清空 selectedId', async () => {
    selectedId.value = `${MANUAL_PREFIX}${firstId}`
    const w = mount(ToolManualPage)
    await w.find('[data-testid="manual-back"]').trigger('click')
    expect(selectedId.value).toBeNull()
  })
  it('未知 id → 兜底文案（不崩溃）', () => {
    selectedId.value = 'manual:ghost'
    const w = mount(ToolManualPage)
    expect(w.find('[data-testid="manual-ghost"]').exists()).toBe(true)
  })
})
