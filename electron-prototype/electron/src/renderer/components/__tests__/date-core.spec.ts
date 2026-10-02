// date-core 单测：与 date-core.golden.json 逐条对拍（Python 参考实现已在 pytest 侧自校验）。
// 黄金文件是双端唯一事实：改口径必须先改参考实现与 JSON，再让 TS 跟上。
import { describe, expect, it } from 'vitest'
import {
  addToDate,
  daysFromToday,
  diffRange,
  formatYMD,
  parseDate,
  todayYMD,
  upcomingAnniversaries,
  type ArithUnit
} from '../../src/date-core'
import golden from '../../src/date-core.golden.json'

describe('diffRange ↔ 黄金用例', () => {
  for (const c of golden.diff_cases) {
    it(`diff: ${c.name}`, () => {
      const a = parseDate(c.a)
      const b = parseDate(c.b)
      expect(a, `parseDate(${c.a})`).not.toBeNull()
      expect(b, `parseDate(${c.b})`).not.toBeNull()
      const r = diffRange(a!, b!)
      expect(r.days).toBe(c.expected.days)
      expect(r.weeks).toBe(c.expected.weeks)
      expect([r.norm.years, r.norm.months, r.norm.days]).toEqual(c.expected.norm)
      expect(r.leapDays).toBe(c.expected.leap_days)
      expect(r.weekday1).toBe(c.expected.weekday_a)
      expect(r.weekday2).toBe(c.expected.weekday_b)
    })
  }
  it('倒序用例标记 swapped，正序不标记', () => {
    expect(diffRange(parseDate('2025-01-01')!, parseDate('2024-01-01')!).swapped).toBe(true)
    expect(diffRange(parseDate('2024-01-01')!, parseDate('2025-01-01')!).swapped).toBe(false)
  })
})

describe('addToDate ↔ 黄金用例', () => {
  for (const c of golden.add_cases) {
    it(`add: ${c.name}`, () => {
      const d = parseDate(c.date)!
      // JSON 导入的字符串字面量被宽化为 string，需收窄回 ArithUnit
      expect(formatYMD(addToDate(d, c.n, c.unit as ArithUnit))).toBe(c.expected)
    })
  }
})

describe('upcomingAnniversaries ↔ 黄金用例', () => {
  for (const c of golden.anniversary_cases) {
    it(`anniv: ${c.name}`, () => {
      const d = parseDate(c.date)!
      const today = parseDate(c.today)!
      const got = upcomingAnniversaries(d, today, c.count)
      expect(got.map((x) => [formatYMD(x.date), x.label])).toEqual(c.expected)
    })
  }
})

describe('日期解析容错', () => {
  it('拒绝非法日期', () => {
    expect(parseDate('2024-02-30')).toBeNull()
    expect(parseDate('2024-2-1')).toBeNull()
    expect(parseDate('2023-02-29')).toBeNull()
    expect(parseDate('')).toBeNull()
    expect(parseDate(undefined)).toBeNull()
  })
  it('接受闰日并原样格式化', () => {
    expect(formatYMD(parseDate('2024-02-29')!)).toBe('2024-02-29')
  })
})

describe('距今', () => {
  it('正=未来 负=已过（注入 today 保证确定性）', () => {
    const today = parseDate('2026-10-02')!
    expect(daysFromToday(parseDate('2027-01-01')!, today)).toBe(91)
    expect(daysFromToday(parseDate('2024-01-01')!, today)).toBe(-1005)
    expect(daysFromToday(parseDate('2026-10-02')!, today)).toBe(0)
  })
  it('todayYMD 缺省取本地今天（不抛错即过）', () => {
    expect(todayYMD().y).toBeGreaterThan(2020)
  })
})
