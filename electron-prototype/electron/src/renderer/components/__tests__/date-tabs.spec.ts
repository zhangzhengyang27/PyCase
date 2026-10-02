// date-calculator 子组件：预设写入聚焦框 / 日历点格两段式设定 / 加减行整数化钳制。
// store 是模块单例：beforeEach 复位（沿用 cards.spec 纪律）。
import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DateRangeInputs from '../date-calculator/DateRangeInputs.vue'
import TabCalendar from '../date-calculator/TabCalendar.vue'
import TabCountdown from '../date-calculator/TabCountdown.vue'
import TabArithmetic from '../date-calculator/TabArithmetic.vue'
import { formatYMD, todayYMD } from '../../src/date-core'
import { arithRows, dateA, dateB } from '../../src/store/interactive'

beforeEach(() => {
  dateA.value = '2024-01-01'
  dateB.value = '2025-01-01'
  arithRows.value = [{ target: 'd1', op: '+', n: 30, unit: 'day' }]
})

describe('DateRangeInputs', () => {
  it('预设写入最近聚焦的日期框（默认 d1）', async () => {
    const w = mount(DateRangeInputs)
    const presets = w.findAll('[data-testid="dc-preset"]')
    await presets[3]!.trigger('click') // 闰年日
    expect(dateA.value).toBe('2024-02-29')
    expect(dateB.value).toBe('2025-01-01')
  })
  it('聚焦 d2 后预设写入 d2', async () => {
    const w = mount(DateRangeInputs)
    await w.find('[data-testid="date-b"]').setValue('2026-03-01')
    await w.find('[data-testid="date-b"]').trigger('focus')
    await w.findAll('[data-testid="dc-preset"]')[0]!.trigger('click')
    // 「今天」写入聚焦的 d2，d1 不被污染
    expect(dateA.value).toBe('2024-01-01')
    expect(dateB.value).toBe(formatYMD(todayYMD()))
  })
  it('交换按钮互换起止', async () => {
    const w = mount(DateRangeInputs)
    await w.find('button[title="交换起止日期"]').trigger('click')
    expect(dateA.value).toBe('2025-01-01')
    expect(dateB.value).toBe('2024-01-01')
  })
  it('非法日期标红（border-danger）', async () => {
    const w = mount(DateRangeInputs)
    await w.find('[data-testid="date-a"]').setValue('')
    expect(w.find('[data-testid="date-a"]').classes().join(' ')).toContain('border-danger')
  })
})

describe('TabCalendar 点格两段式', () => {
  it('第一次点设起点，第二次点设终点', async () => {
    const w = mount(TabCalendar)
    // 复位后左月=2024-01（dateA），右月=2024-02——点格在可见双月内取
    await w.find('[data-testid="cal-2024-01-15"]').trigger('click')
    expect(dateA.value).toBe('2024-01-15')
    await w.find('[data-testid="cal-2024-02-20"]').trigger('click')
    expect(dateB.value).toBe('2024-02-20')
  })
  it('翻月游标：前翻/后翻改变左侧月份', async () => {
    const w = mount(TabCalendar)
    expect(w.text()).toContain('2024 年 1 月')
    await w.find('[data-testid="cal-next"]').trigger('click')
    expect(w.text()).toContain('2024 年 2 月')
    await w.find('[data-testid="cal-prev"]').trigger('click')
    expect(w.text()).toContain('2024 年 1 月')
  })
})

describe('TabCountdown', () => {
  it('过去日期：显示「已过」+ 纪念日前瞻（满/周年）', () => {
    const w = mount(TabCountdown)
    const text = w.find('[data-testid="cd-a"]').text()
    expect(text).toContain('已过')
    expect(text).toMatch(/周年|满/)
  })
  it('无效日期：cd-a 显示「无效日期」', () => {
    dateA.value = ''
    const w = mount(TabCountdown)
    expect(w.find('[data-testid="cd-a"]').text()).toContain('无效日期')
    // d2 仍有效，正常渲染
    expect(w.find('[data-testid="cd-b"]').text()).toContain('2025-01-01')
  })
})

describe('TabArithmetic', () => {
  it('行结果即时计算（d1 +30 day → 2024-01-31）', () => {
    const w = mount(TabArithmetic)
    expect(w.find('[data-testid="arith-result"]').text()).toContain('2024-01-31')
  })
  it('小数输入被钳制为整数（兜底路径）', async () => {
    arithRows.value = [{ target: 'd1', op: '+', n: 2.7, unit: 'day' }]
    const w = mount(TabArithmetic)
    // 兜底钳制：结果按 2 天算 → 2024-01-03
    expect(w.find('[data-testid="arith-result"]').text()).toContain('2024-01-03')
  })
  it('增删行', async () => {
    const w = mount(TabArithmetic)
    await w.find('[data-testid="arith-add"]').trigger('click')
    expect(arithRows.value).toHaveLength(2)
    await w.find('[data-testid="arith-row-0"] button[aria-label="删除第 1 行"]').trigger('click')
    expect(arithRows.value).toHaveLength(1)
  })
})
