// DateCalculatorPage 组装：Tab 切换、无效日期引导、返回清 selectedId、自动交换提示。
// store 是模块单例：每个用例前复位（沿用 cards.spec 的纪律）。
import { beforeEach, describe, expect, it, vi } from 'vitest'

// CodeDrawer 顶层 import monaco——jsdom 下用假实现替身（与 code-drawer.spec 同一策略）
vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

import { mount } from '@vue/test-utils'
import DateCalculatorPage from '../date-calculator/DateCalculatorPage.vue'
import { activeTab, arithRows, dateA, dateB } from '../../src/store/interactive'
import { selectedId } from '../../src/store/detail'

beforeEach(() => {
  dateA.value = '2024-01-01'
  dateB.value = '2025-01-01'
  activeTab.value = 'diff'
  arithRows.value = [{ target: 'd1', op: '+', n: 30, unit: 'day' }]
  selectedId.value = 'interactive:date-calculator'
})

describe('DateCalculatorPage', () => {
  it('默认日期差 Tab：大数字 366 天', () => {
    const w = mount(DateCalculatorPage)
    expect(w.find('[data-testid="diff-days"]').text()).toContain('366')
  })
  it('无效日期显示引导文案', () => {
    dateA.value = ''
    const w = mount(DateCalculatorPage)
    expect(w.text()).toContain('请补全两个有效日期')
  })
  it('Tab 切换写入 store（会话内记忆）', async () => {
    const w = mount(DateCalculatorPage)
    await w.find('[data-testid="tab-calendar"]').trigger('click')
    expect(activeTab.value).toBe('calendar')
  })
  it('倒序输入出现自动交换提示', () => {
    dateA.value = '2025-01-01'
    dateB.value = '2024-01-01'
    const w = mount(DateCalculatorPage)
    expect(w.find('[data-testid="swap-hint"]').exists()).toBe(true)
  })
  it('返回按钮清空 selectedId', async () => {
    const w = mount(DateCalculatorPage)
    await w.find('[data-testid="dc-back"]').trigger('click')
    expect(selectedId.value).toBeNull()
  })
})
