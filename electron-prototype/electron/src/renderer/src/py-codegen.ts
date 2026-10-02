// py-codegen.ts：按 Tab 生成等价 Python 代码（纯模板拼接，无失败路径）。
// 产物必须是可直接 python3 运行的完整脚本，输出与页面计算一致（纯标准库）。
import { type ArithUnit, type DateYMD, formatYMD } from './date-core'

const dq = (v: DateYMD) => `date(${v.y}, ${v.m}, ${v.d})`

export function genDiffCode(a: DateYMD, b: DateYMD): string {
  return `"""日期计算：${formatYMD(a)} 与 ${formatYMD(b)} 之间隔多少天。"""
from datetime import date

d1 = ${dq(a)}
d2 = ${dq(b)}
diff = abs((d2 - d1).days)
print(f"间隔 {diff} 天（约 {diff / 7:.1f} 周）")
print("各自星期:", d1.strftime("%A"), "/", d2.strftime("%A"))
`
}

export function genCountdownCode(a: DateYMD, b: DateYMD): string {
  return `"""正倒计时：${formatYMD(a)} 与 ${formatYMD(b)} 距今天数。"""
from datetime import date

today = date.today()
d1 = ${dq(a)}
d2 = ${dq(b)}
print("d1 距今:", (d1 - today).days, "天")
print("d2 距今:", (d2 - today).days, "天")
`
}

export function genCalendarCode(a: DateYMD, b: DateYMD): string {
  return `"""日历：打印 ${a.y} 年 ${a.m} 月月历与起止日期的星期。"""
import calendar
from datetime import date

WD = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
d1 = ${dq(a)}
d2 = ${dq(b)}
print(calendar.month(${a.y}, ${a.m}))
print("d1 星期:", WD[d1.weekday()], "| d2 星期:", WD[d2.weekday()])
`
}

export interface ArithRowLike {
  target: 'd1' | 'd2'
  op: '+' | '-'
  n: number
  unit: ArithUnit
}

const HELPER = `def add_months(d, n):
    total = d.year * 12 + (d.month - 1) + n
    y, m0 = divmod(total, 12)
    return date(y, m0 + 1, min(d.day, calendar.monthrange(y, m0 + 1)[1]))


def add_years(d, n):
    y = d.year + n
    return date(y, d.month, min(d.day, calendar.monthrange(y, d.month)[1]))`

export function genArithCode(a: DateYMD, b: DateYMD, rows: ArithRowLike[]): string {
  const needsHelper = rows.some((r) => r.unit === 'month' || r.unit === 'year')
  const body = rows.map((r) => {
    const signed = r.op === '+' ? r.n : -r.n
    const label = `${r.target} ${r.op}${Math.abs(r.n)} ${r.unit}`
    if (r.unit === 'month' || r.unit === 'year') {
      const fn = r.unit === 'month' ? 'add_months' : 'add_years'
      return `print("${label} →", ${fn}(${r.target}, ${signed}).isoformat())`
    }
    const arg = r.unit === 'week' ? 'weeks' : 'days'
    const op = signed >= 0 ? '+' : '-'
    return `print("${label} →", (${r.target} ${op} timedelta(${arg}=${Math.abs(signed)})).isoformat())`
  })
  return `"""日期加减：对 ${formatYMD(a)} / ${formatYMD(b)} 做增减。"""
from datetime import date, timedelta
${needsHelper ? '\nimport calendar\n\n\n' + HELPER + '\n' : ''}
d1 = ${dq(a)}
d2 = ${dq(b)}
${body.join('\n')}
`
}
