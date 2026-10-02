// py-codegen：生成的 Python 代码必须是可直接运行的完整脚本，且日期实参随输入变化。
import { describe, expect, it } from 'vitest'
import { parseDate } from '../../src/date-core'
import { genArithCode, genCalendarCode, genCountdownCode, genDiffCode } from '../../src/py-codegen'

const a = parseDate('2024-01-01')!
const b = parseDate('2025-01-01')!

describe('生成代码包含当前输入', () => {
  it('日期差', () => {
    const code = genDiffCode(a, b)
    expect(code).toContain('d1 = date(2024, 1, 1)')
    expect(code).toContain('d2 = date(2025, 1, 1)')
    expect(code).toContain('(d2 - d1).days')
    expect(code).toContain('strftime')
  })
  it('正倒计时', () => {
    const code = genCountdownCode(a, b)
    expect(code).toContain('date.today()')
    expect(code).toContain('(d1 - today).days')
  })
  it('日历', () => {
    const code = genCalendarCode(a, b)
    expect(code).toContain('calendar.month(2024, 1)')
  })
  it('日期加减：timedelta 行 + clamp helper 按需出现', () => {
    const plain = genArithCode(a, b, [{ target: 'd1', op: '+', n: 30, unit: 'day' }])
    expect(plain).toContain('timedelta(days=30)')
    expect(plain).not.toContain('def add_months')
    const clamped = genArithCode(a, b, [
      { target: 'd2', op: '-', n: 2, unit: 'week' },
      { target: 'd1', op: '+', n: 1, unit: 'month' }
    ])
    expect(clamped).toContain('timedelta(weeks=2)')
    expect(clamped).toContain('add_months(d1, 1)')
    expect(clamped).toContain('def add_months')
  })
})
