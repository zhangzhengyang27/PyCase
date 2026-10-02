// py-codegen.ts：按 Tab 生成等价 Python 代码（纯模板拼接，无失败路径）。
// 产物必须是可直接 python3 运行的完整脚本，输出与页面计算一致（纯标准库）。
import { type ArithUnit, type DateYMD, formatYMD } from './date-core'

const dq = (v: DateYMD) => `date(${v.y}, ${v.m}, ${v.d})`

export function genDiffCode(a: DateYMD, b: DateYMD): string {
  // 星期输出走 WD 元组而非 strftime("%A")：后者 locale 相关（且为英文），与页面中文口径不一致。
  return `"""日期计算：${formatYMD(a)} 与 ${formatYMD(b)} 之间隔多少天。"""
from datetime import date

WD = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
d1 = ${dq(a)}
d2 = ${dq(b)}
diff = abs((d2 - d1).days)
print(f"间隔 {diff} 天（约 {diff / 7:.1f} 周）")
print("各自星期:", WD[d1.weekday()], "/", WD[d2.weekday()])
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

const HELP_ADD_MONTHS = `def add_months(d, n):
    total = d.year * 12 + (d.month - 1) + n
    y, m0 = divmod(total, 12)
    return date(y, m0 + 1, min(d.day, calendar.monthrange(y, m0 + 1)[1]))`

const HELP_ADD_YEARS = `def add_years(d, n):
    y = d.year + n
    return date(y, d.month, min(d.day, calendar.monthrange(y, d.month)[1]))`

export function genArithCode(a: DateYMD, b: DateYMD, rows: ArithRowLike[]): string {
  // helper 按需输出：只带 rows 实际用到的 clamp 函数（只用月的脚本不带 add_years，反之亦然）。
  const needsMonths = rows.some((r) => r.unit === 'month')
  const needsYears = rows.some((r) => r.unit === 'year')
  const body = rows.map((r) => {
    const signed = r.op === '+' ? r.n : -r.n
    // 标签从 signed 推导，与实际运算方向一致（op '+' 配负 n 就是减法，必须显示 "-"）
    const label = `${r.target} ${signed < 0 ? '-' : '+'}${Math.abs(signed)} ${r.unit}`
    if (r.unit === 'month' || r.unit === 'year') {
      const fn = r.unit === 'month' ? 'add_months' : 'add_years'
      return `print("${label} →", ${fn}(${r.target}, ${signed}).isoformat())`
    }
    const arg = r.unit === 'week' ? 'weeks' : 'days'
    const op = signed >= 0 ? '+' : '-'
    return `print("${label} →", (${r.target} ${op} timedelta(${arg}=${Math.abs(signed)})).isoformat())`
  })
  // PEP8：两个 stdlib import 归同一组（组内不空行）；顶层 def 之间、def 与正文之间空两行。
  const helpers = [needsMonths ? HELP_ADD_MONTHS : '', needsYears ? HELP_ADD_YEARS : ''].filter(Boolean).join('\n\n\n')
  const imports =
    needsMonths || needsYears
      ? `from datetime import date, timedelta\nimport calendar\n\n\n${helpers}\n\n\n`
      : `from datetime import date, timedelta\n\n`
  return `"""日期加减：对 ${formatYMD(a)} / ${formatYMD(b)} 做增减。"""
${imports}d1 = ${dq(a)}
d2 = ${dq(b)}
${body.join('\n')}
`
}
