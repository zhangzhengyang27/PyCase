// date-core.ts：日期计算器纯计算核心（无 DOM / store / 三方依赖）。
// 口径唯一实现；与 Python datetime 参考实现以 date-core.golden.json 对拍
// （tests/test_date_core_golden.py 自校验 + 本侧 vitest）。全部计算走 UTC 毫秒
// 避免时区偏移；「今天」取本地日期且可注入（测试与对拍确定性）。
export interface DateYMD {
  y: number
  m: number
  d: number
}

const MS_DAY = 86_400_000
// 下标 0 = 星期一（与 getUTCDay 的 0=周日 错位，取值时做 (wd+6)%7 映射）
const WD_ZH = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']

export function parseDate(s: string | undefined | null): DateYMD | null {
  if (!s) return null
  const mt = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s.trim())
  if (!mt) return null
  const y = Number(mt[1])
  const m = Number(mt[2])
  const d = Number(mt[3])
  if (m < 1 || m > 12 || d < 1) return null
  const ms = Date.UTC(y, m - 1, d)
  const back = new Date(ms)
  // 回读校验自然排除 2 月 30 日、非闰年 2 月 29 日等
  if (back.getUTCFullYear() !== y || back.getUTCMonth() !== m - 1 || back.getUTCDate() !== d) return null
  return { y, m, d }
}

export function formatYMD(v: DateYMD): string {
  const p2 = (n: number) => String(n).padStart(2, '0')
  return `${v.y}-${p2(v.m)}-${p2(v.d)}`
}

function utcMs(v: DateYMD): number {
  return Date.UTC(v.y, v.m - 1, v.d)
}

function fromUtcMs(ms: number): DateYMD {
  const t = new Date(ms)
  return { y: t.getUTCFullYear(), m: t.getUTCMonth() + 1, d: t.getUTCDate() }
}

/** 天数差 b - a（负值表示 b 在前） */
export function daysBetween(a: DateYMD, b: DateYMD): number {
  return Math.round((utcMs(b) - utcMs(a)) / MS_DAY)
}

export interface NormalizedRange {
  d1: DateYMD
  d2: DateYMD
  swapped: boolean
}

/** 规范化区间：恒返回 d1 <= d2，swapped 标记输入是否倒序 */
export function normalizeRange(a: DateYMD, b: DateYMD): NormalizedRange {
  return daysBetween(a, b) >= 0 ? { d1: a, d2: b, swapped: false } : { d1: b, d2: a, swapped: true }
}

export function weekdayZh(v: DateYMD): string {
  const wd = new Date(utcMs(v)).getUTCDay() // 0=周日 … 6=周六
  return WD_ZH[(wd + 6) % 7]
}

function isLeap(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0
}

function lastDayOfMonth(y: number, m: number): number {
  return [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
}

export function addDays(v: DateYMD, n: number): DateYMD {
  return fromUtcMs(utcMs(v) + n * MS_DAY)
}

/** 加 N 月：日取 min(原日, 目标月最后一日)（clamp；闰日随动：2024-02-29 + 1 年 = 2025-02-28） */
export function addMonths(v: DateYMD, n: number): DateYMD {
  const total = v.y * 12 + (v.m - 1) + n
  const y = Math.floor(total / 12)
  const m = (((total % 12) + 12) % 12) + 1
  return { y, m, d: Math.min(v.d, lastDayOfMonth(y, m)) }
}

export function addYears(v: DateYMD, n: number): DateYMD {
  const y = v.y + n
  return { y, m: v.m, d: Math.min(v.d, lastDayOfMonth(y, v.m)) }
}

export type ArithUnit = 'day' | 'week' | 'month' | 'year'

export function addToDate(v: DateYMD, n: number, unit: ArithUnit): DateYMD {
  if (unit === 'day') return addDays(v, n)
  if (unit === 'week') return addDays(v, n * 7)
  if (unit === 'month') return addMonths(v, n)
  return addYears(v, n)
}

/** 左闭右开 [d1, d2) 内 2 月 29 日个数 */
export function leapDaysBetween(a: DateYMD, b: DateYMD): number {
  const { d1, d2 } = normalizeRange(a, b)
  let count = 0
  for (let y = d1.y; y <= d2.y; y++) {
    if (!isLeap(y)) continue
    const leap: DateYMD = { y, m: 2, d: 29 }
    if (daysBetween(d1, leap) >= 0 && daysBetween(leap, d2) > 0) count++
  }
  return count
}

export interface NormYMD {
  years: number
  months: number
  days: number
}

/** 规范化年/月/天：整月按周年锚定（d2.日 < d1.日 回退一个月），余数天 = 锚点加整月到 d2 */
export function normYMD(a: DateYMD, b: DateYMD): NormYMD {
  const { d1, d2 } = normalizeRange(a, b)
  let months = (d2.y - d1.y) * 12 + (d2.m - d1.m)
  if (d2.d < d1.d) months -= 1
  const anchor = addMonths(d1, months)
  return {
    years: Math.floor(months / 12),
    months: ((months % 12) + 12) % 12,
    days: daysBetween(anchor, d2)
  }
}

export interface DiffResult {
  days: number
  weeks: string
  norm: NormYMD
  leapDays: number
  weekday1: string
  weekday2: string
  swapped: boolean
}

export function diffRange(a: DateYMD, b: DateYMD): DiffResult {
  const { d1, d2, swapped } = normalizeRange(a, b)
  const days = daysBetween(d1, d2)
  return {
    days,
    weeks: (days / 7).toFixed(1),
    norm: normYMD(d1, d2),
    leapDays: leapDaysBetween(d1, d2),
    weekday1: weekdayZh(d1),
    weekday2: weekdayZh(d2),
    swapped
  }
}

/** 本地时区「今天」，可注入 now 供测试 */
export function todayYMD(now?: Date): DateYMD {
  const t = now ?? new Date()
  return { y: t.getFullYear(), m: t.getMonth() + 1, d: t.getDate() }
}

/** 距今天数：正 = 未来，负 = 已过去 */
export function daysFromToday(v: DateYMD, today?: DateYMD): number {
  return daysBetween(today ?? todayYMD(), v)
}

export interface Anniversary {
  date: DateYMD
  label: string
}

/** 纪念日前瞻：从 d 起第 k×100 天（「满 N 天」）与第 k 周年（clamp 加年）中，
 *  日期 >= today 的未来最近 count 个（升序；同日非周年在前）。
 *  与 tests/test_date_core_golden.py 的参考实现同构，改动必须双侧同步。 */
export function upcomingAnniversaries(d: DateYMD, today: DateYMD, count = 3): Anniversary[] {
  const cands: Array<{ date: DateYMD; label: string; yearly: boolean }> = []
  const k0 = Math.max(1, Math.ceil(daysBetween(d, today) / 100))
  for (let k = k0; k < k0 + 8; k++) {
    cands.push({ date: addDays(d, 100 * k), label: `满 ${100 * k} 天`, yearly: false })
  }
  const y0 = Math.max(1, today.y - d.y - 1)
  let taken = 0
  for (let k = y0; taken < 8 && k < y0 + 20; k++) {
    const anniv = addYears(d, k)
    // anniv >= today 才保留（daysBetween(a,b)=b-a，故 <=0 即成立）
    if (daysBetween(anniv, today) <= 0) {
      cands.push({ date: anniv, label: `${k} 周年`, yearly: true })
      taken++
    }
  }
  // daysBetween(a, b) = b - a，升序须传 (z, x) 让更早者排前
  cands.sort(
    (x, z) =>
      daysBetween(z.date, x.date) || (x.yearly === z.yearly ? x.label.localeCompare(z.label) : x.yearly ? 1 : -1)
  )
  const out: Anniversary[] = []
  const seen = new Set<string>()
  // 防御性去重：两类候选日期理论不相交，仅为口径健壮
  for (const c of cands) {
    const key = formatYMD(c.date)
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ date: c.date, label: c.label })
    if (out.length >= count) break
  }
  return out
}
