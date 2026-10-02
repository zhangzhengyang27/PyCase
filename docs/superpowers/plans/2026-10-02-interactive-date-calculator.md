# 日期计算器（交互式页面工具）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「语言基础」5 个静态日期变体升级为工具箱里的「日期计算器」交互工具：工具箱卡片 + 专属交互页（四 Tab + 折叠代码抽屉），纯前端即时计算，生成的 Python 代码可通过 sidecar 真实运行；5 个旧变体从生成器与库中退役。

**Architecture:** 前端注册表 `interactive-tools.ts` 提供卡片元数据并由 `catalog.ts` 合并进工具池（客户端匹配搜索/收藏，恒置顶）；`selectedId` 命中 `interactive:` 前缀时 App.vue 渲染 `DateCalculatorPage` 而非 DetailPage。计算核心 `date-core.ts`（纯函数）与 Python datetime 参考实现以 `date-core.golden.json` 双端对拍。抽屉「运行」通过 sidecar `run_example` 新增的可选 `code` 参数在一次性 adhoc 工作区执行（不落真相源）。

**Tech Stack:** Vue 3 `<script setup>` + theme.css v3 tokens、现有 base 组件、vitest + @vue/test-utils、Monaco（只读独立实例）、Python sidecar（JSON-RPC over stdio）、pytest。

**规格来源:** `docs/superpowers/specs/2026-10-02-interactive-date-calculator-design.md`（已批准）。分支：`feat/interactive-date-calculator`。

**工作目录约定:** 渲染层命令在 `electron-prototype/electron/` 下执行（`npm run …` / `npx vitest`）；Python 命令在仓库根执行，优先用 `.venv/bin/python`（不存在则 `python3`）。

---

## 文件结构总览

```
electron-prototype/electron/src/renderer/
├── src/
│   ├── date-core.ts                  # 新建：纯计算核心（口径唯一实现）
│   ├── date-core.golden.json         # 新建：TS↔Python 双端黄金用例
│   ├── py-codegen.ts                 # 新建：各 Tab 的 Python 代码模板（纯函数）
│   ├── interactive-tools.ts          # 新建：交互工具注册表（卡片元数据）
│   ├── store/
│   │   ├── catalog.ts                # 修改：toolboxItems 合并交互工具；toolsTotal/catalogToolsTotal
│   │   ├── interactive.ts            # 新建：日期对/Tab/加减行状态 + open/close
│   │   └── date-run.ts               # 新建：抽屉运行（runExample+code，事件过滤）
│   ├── section-icons.ts              # 修改：TOOLBOX_ICONS 加 'interactive'
│   └── __tests__/ (vitest 单测，与组件测试同目录约定)
├── components/
│   ├── ExampleCard.vue               # 修改：interactive 形态（隐藏运行/质量分，显示「交互」徽章）
│   ├── ToolboxView.vue               # 修改：交互工具分组置顶 + onOpen 分支
│   ├── App.vue                       # 修改：interactive: 前缀渲染 DateCalculatorPage
│   └── date-calculator/              # 新建目录：页面与子组件
│       ├── DateCalculatorPage.vue
│       ├── DateRangeInputs.vue
│       ├── TabDiff.vue / TabCountdown.vue / TabArithmetic.vue / TabCalendar.vue
│       └── CodeDrawer.vue
electron-prototype/
├── shared/protocol.ts                # 修改：RunExampleParams 可选 code
├── electron/src/preload/index.ts     # 修改：runExample 类型加 code
└── sidecar/server.py                 # 修改：code 校验 + adhoc 工作区分支

（仓库根）
├── scripts/gen_bulk_examples.py      # 修改：删除 date-diff 模板
├── tests/test_date_core_golden.py    # 新建：黄金用例 Python 参考实现自校验
├── tests/test_guard_protocol.py      # 修改：code 覆盖运行的守卫用例
└── json_examples/                    # 重生成：bulk_basics.json 99→94，删 5 个 date-diff .py
```

---

### Task 0: 收存工作区遗留改动

仓库当前有用户未提交改动（`BrowseToolbar.vue`、两个组件测试、`tests/test_guard_data.py` 新增护栏、已删除的 `sidecar.spec`）。其中 `tests/test_guard_data.py` 与本特性的退役工作会交汇，必须先单独收存，严禁混入本特性提交。

- [ ] **Step 1: 确认遗留改动内容与预期相符**

Run: `git status --short && git diff --stat`
Expected: 恰好 5 个文件（`electron-prototype/electron/build-pyinstaller/sidecar.spec` 删除、`BrowseToolbar.vue`、`browse.spec.ts`、`cards.spec.ts`、`tests/test_guard_data.py`）。若有其他文件混入，停下来向用户确认。

- [ ] **Step 2: 全部收存为一个独立提交**

```bash
git add -A
git commit -m "chore: 收存工作区遗留改动（可运行性下拉退役收尾 + 占位符残留护栏）"
```

---

### Task 1: 黄金用例文件 + date-core.ts（TDD）

**Files:**
- Create: `electron-prototype/electron/src/renderer/src/date-core.golden.json`
- Create: `electron-prototype/electron/src/renderer/src/date-core.ts`
- Test: `electron-prototype/electron/src/renderer/components/__tests__/date-core.spec.ts`

- [ ] **Step 1: 写黄金用例文件**（expected 值已用 Python datetime 参考实现算出，禁止改动数值）

`electron-prototype/electron/src/renderer/src/date-core.golden.json`：

```json
{
 "comment": "date-core 双端黄金用例：expected 由 Python datetime 参考实现生成并自校验（tests/test_date_core_golden.py），TS 侧 vitest 断言 date-core.ts 与之完全一致。weeks 为一位小数字符串；norm 为 [年, 月, 天]；闰日口径 = 左闭右开 [d1, d2)；倒序用例的 weekday_* 是规范化后 d1/d2 的星期。",
 "diff_cases": [
  {"name": "跨闰年", "a": "2024-01-01", "b": "2025-01-01",
   "expected": {"days": 366, "weeks": "52.3", "norm": [1, 0, 0], "leap_days": 1, "weekday_a": "星期一", "weekday_b": "星期三"}},
  {"name": "闰日起点", "a": "2020-02-29", "b": "2026-02-28",
   "expected": {"days": 2191, "weeks": "313.0", "norm": [5, 11, 30], "leap_days": 2, "weekday_a": "星期六", "weekday_b": "星期六"}},
  {"name": "跨年界", "a": "2023-12-31", "b": "2026-01-01",
   "expected": {"days": 732, "weeks": "104.6", "norm": [2, 0, 1], "leap_days": 1, "weekday_a": "星期日", "weekday_b": "星期四"}},
  {"name": "同日", "a": "2026-09-22", "b": "2026-09-22",
   "expected": {"days": 0, "weeks": "0.0", "norm": [0, 0, 0], "leap_days": 0, "weekday_a": "星期二", "weekday_b": "星期二"}},
  {"name": "倒序输入自动交换", "a": "2025-01-01", "b": "2024-01-01",
   "expected": {"days": 366, "weeks": "52.3", "norm": [1, 0, 0], "leap_days": 1, "weekday_a": "星期一", "weekday_b": "星期三"}},
  {"name": "同年短距", "a": "2026-09-01", "b": "2026-10-02",
   "expected": {"days": 31, "weeks": "4.4", "norm": [0, 1, 1], "leap_days": 0, "weekday_a": "星期二", "weekday_b": "星期五"}}
 ],
 "add_cases": [
  {"name": "加月clamp月末", "date": "2024-01-31", "n": 1, "unit": "month", "expected": "2024-02-29"},
  {"name": "闰日加年clamp", "date": "2024-02-29", "n": 1, "unit": "year", "expected": "2025-02-28"},
  {"name": "减一周", "date": "2026-01-08", "n": -1, "unit": "week", "expected": "2026-01-01"},
  {"name": "加一天", "date": "2024-12-31", "n": 1, "unit": "day", "expected": "2025-01-01"}
 ],
 "anniversary_cases": [
  {"name": "过去日期未来里程碑", "date": "2024-01-01", "today": "2026-10-02", "count": 3,
   "expected": [["2027-01-01", "3 周年"], ["2027-01-05", "满 1100 天"], ["2027-04-15", "满 1200 天"]]},
  {"name": "闰日已过久远", "date": "2020-02-29", "today": "2026-10-02", "count": 3,
   "expected": [["2027-01-03", "满 2500 天"], ["2027-02-28", "7 周年"], ["2027-04-13", "满 2600 天"]]},
  {"name": "未来日期倒计时", "date": "2027-01-01", "today": "2026-10-02", "count": 3,
   "expected": [["2027-04-11", "满 100 天"], ["2027-07-20", "满 200 天"], ["2027-10-28", "满 300 天"]]}
 ]
}
```

- [ ] **Step 2: 确认 tsconfig 允许 JSON 导入**

Run: `grep -n "resolveJsonModule" electron-prototype/electron/tsconfig.web.json`
若无输出，编辑 `tsconfig.web.json` 的 `compilerOptions` 加入 `"resolveJsonModule": true`。

- [ ] **Step 3: 写失败测试**

`electron-prototype/electron/src/renderer/components/__tests__/date-core.spec.ts`：

```ts
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
  upcomingAnniversaries
} from '../src/date-core'
import golden from '../src/date-core.golden.json'

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
      expect(formatYMD(addToDate(d, c.n, c.unit))).toBe(c.expected)
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
    expect(daysFromToday(parseDate('2024-01-01')!, today)).toBe(-639)
    expect(daysFromToday(parseDate('2026-10-02')!, today)).toBe(0)
  })
  it('todayYMD 缺省取本地今天（不抛错即过）', () => {
    expect(todayYMD().y).toBeGreaterThan(2020)
  })
})
```

- [ ] **Step 4: 运行测试确认失败**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/date-core.spec.ts`
Expected: FAIL，报 `Cannot find module '../src/date-core'`。

- [ ] **Step 5: 实现 date-core.ts**

`electron-prototype/electron/src/renderer/src/date-core.ts`：

```ts
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
    const a = addYears(d, k)
    if (daysBetween(a, today) <= 0) {
      cands.push({ date: a, label: `${k} 周年`, yearly: true })
      taken++
    }
  }
  cands.sort(
    (x, z) =>
      daysBetween(x.date, z.date) ||
      (x.yearly === z.yearly ? x.label.localeCompare(z.label) : x.yearly ? 1 : -1)
  )
  const out: Anniversary[] = []
  const seen = new Set<string>()
  for (const c of cands) {
    const key = formatYMD(c.date)
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ date: c.date, label: c.label })
    if (out.length >= count) break
  }
  return out
}
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/date-core.spec.ts`
Expected: PASS（全部用例绿）。若黄金值断言失败，**先怀疑实现**，逐条核对口径；确认实现无误后仍失败才复核黄金文件数值（用 `python3` 按 Task 2 参考实现重算）。

- [ ] **Step 7: typecheck**

Run: `cd electron-prototype/electron && npm run typecheck`
Expected: 无错误（JSON 导入类型解析成功）。

- [ ] **Step 8: Commit**

```bash
git add electron-prototype/electron/src/renderer/src/date-core.ts \
        electron-prototype/electron/src/renderer/src/date-core.golden.json \
        electron-prototype/electron/src/renderer/components/__tests__/date-core.spec.ts \
        electron-prototype/electron/tsconfig.web.json
git commit -m "feat(date-tool): date-core 纯计算核心 + 双端黄金用例（vitest 侧）"
```

---

### Task 2: 黄金用例 Python 参考实现自校验（pytest 侧）

**Files:**
- Test: `tests/test_date_core_golden.py`

- [ ] **Step 1: 写参考实现与自校验测试**

`tests/test_date_core_golden.py`：

```python
"""date-core 黄金用例参考实现自校验（TS ↔ Python 对拍的 Python 侧）。

date-core.golden.json 是双端唯一事实：expected 由本文件的 datetime 参考实现
计算并在此断言（防手改漂移）；TS 侧由 vitest（components/__tests__/date-core.spec.ts）
断言 date-core.ts 输出与同一文件一致。改口径的顺序：先改参考实现并重算 JSON，
再同步 TS 实现，双侧测试同时转绿。
"""

import calendar as _cal
import json
import math
from datetime import date, timedelta
from pathlib import Path

GOLDEN = (
    Path(__file__).resolve().parent.parent
    / "electron-prototype" / "electron" / "src" / "renderer" / "src" / "date-core.golden.json"
)
WD = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def _p(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def _add_months(d: date, k: int) -> date:
    total = d.year * 12 + (d.month - 1) + k
    y, m0 = divmod(total, 12)
    return date(y, m0 + 1, min(d.day, _cal.monthrange(y, m0 + 1)[1]))


def _add_years(d: date, k: int) -> date:
    y = d.year + k
    return date(y, d.month, min(d.day, _cal.monthrange(y, d.month)[1]))


def ref_diff(a: date, b: date) -> dict:
    if b < a:
        a, b = b, a
    days = (b - a).days
    m = (b.year - a.year) * 12 + (b.month - a.month)
    if b.day < a.day:
        m -= 1
    rem = (b - _add_months(a, m)).days
    leap = sum(
        1
        for y in range(a.year, b.year + 1)
        if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) and date(y, 2, 29) >= a and date(y, 2, 29) < b
    )
    return {
        "days": days,
        "weeks": f"{days / 7:.1f}",
        "norm": [m // 12, m % 12, rem],
        "leap_days": leap,
        "weekday_a": WD[a.weekday()],
        "weekday_b": WD[b.weekday()],
    }


def ref_add(s: str, n: int, unit: str) -> str:
    d = _p(s)
    if unit == "day":
        r = d + timedelta(days=n)
    elif unit == "week":
        r = d + timedelta(days=7 * n)
    elif unit == "month":
        r = _add_months(d, n)
    else:
        r = _add_years(d, n)
    return r.isoformat()


def ref_anniv(s: str, today: str, count: int = 3) -> list:
    d, t = _p(s), _p(today)
    cands = []
    k0 = max(1, math.ceil((t - d).days / 100))
    cands += [(d + timedelta(days=100 * k), f"满 {100 * k} 天") for k in range(k0, k0 + 8)]
    y0 = max(1, t.year - d.year - 1)
    got = 0
    for k in range(y0, y0 + 20):
        if got >= 8:
            break
        a = _add_years(d, k)
        if a >= t:
            cands.append((a, f"{k} 周年"))
            got += 1
    cands.sort(key=lambda pair: (pair[0], "周" in pair[1]))
    out, used = [], set()
    for dt, label in cands:
        if dt in used:
            continue
        used.add(dt)
        out.append([dt.isoformat(), label])
        if len(out) == count:
            break
    return out


def _load() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_diff_cases_match_reference():
    for c in _load()["diff_cases"]:
        got = ref_diff(_p(c["a"]), _p(c["b"]))
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_add_cases_match_reference():
    for c in _load()["add_cases"]:
        got = ref_add(c["date"], c["n"], c["unit"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_anniversary_cases_match_reference():
    for c in _load()["anniversary_cases"]:
        got = ref_anniv(c["date"], c["today"], c["count"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_golden_has_all_sections():
    data = _load()
    assert len(data["diff_cases"]) >= 5
    assert len(data["add_cases"]) >= 4
    assert len(data["anniversary_cases"]) >= 3
```

- [ ] **Step 2: 运行确认通过**

Run: `(.venv/bin/python || python3) -m pytest tests/test_date_core_golden.py -q`
Expected: `4 passed`。任何失败说明黄金文件与参考实现不符——以参考实现为准修正 JSON 数值，并回到 Task 1 让 vitest 同步。

- [ ] **Step 3: Commit**

```bash
git add tests/test_date_core_golden.py
git commit -m "test(date-tool): 黄金用例 Python 参考实现自校验（对拍 pytest 侧）"
```

---

### Task 3: py-codegen.ts 代码模板（TDD）

**Files:**
- Create: `electron-prototype/electron/src/renderer/src/py-codegen.ts`
- Test: `electron-prototype/electron/src/renderer/components/__tests__/py-codegen.spec.ts`

- [ ] **Step 1: 写失败测试**

`electron-prototype/electron/src/renderer/components/__tests__/py-codegen.spec.ts`：

```ts
// py-codegen：生成的 Python 代码必须是可直接运行的完整脚本，且日期实参随输入变化。
import { describe, expect, it } from 'vitest'
import { parseDate } from '../src/date-core'
import { genArithCode, genCalendarCode, genCountdownCode, genDiffCode } from '../src/py-codegen'

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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/py-codegen.spec.ts`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 py-codegen.ts**

`electron-prototype/electron/src/renderer/src/py-codegen.ts`：

```ts
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
```

- [ ] **Step 4: 运行测试与真实运行抽查**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/py-codegen.spec.ts`
Expected: PASS。

另抽查产物可运行（用 node 把同一模板跑一次 python3）：

```bash
cd electron-prototype/electron && node -e "
const { genDiffCode, genArithCode } = await import('./src/renderer/src/py-codegen.ts').catch(() => ({}));
" 2>/dev/null || true
```
（上面这步只是探路；**可靠的抽查是手写一个临时脚本**）：

```bash
cd /tmp && cat > chk.py <<'EOF'
from datetime import date, timedelta
import calendar
d1 = date(2024, 1, 1)
d2 = date(2025, 1, 1)
diff = abs((d2 - d1).days)
print(f"间隔 {diff} 天（约 {diff / 7:.1f} 周）")
EOF
python3 chk.py && rm chk.py
```
Expected: `间隔 366 天（约 52.3 周）`。

- [ ] **Step 5: Commit**

```bash
git add electron-prototype/electron/src/renderer/src/py-codegen.ts \
        electron-prototype/electron/src/renderer/components/__tests__/py-codegen.spec.ts
git commit -m "feat(date-tool): 四 Tab 等价 Python 代码模板（py-codegen）"
```

---

### Task 4: interactive-tools 注册表 + catalog 合并（TDD）

**Files:**
- Create: `electron-prototype/electron/src/renderer/src/interactive-tools.ts`
- Modify: `electron-prototype/electron/src/renderer/src/store/catalog.ts`（`toolboxItems` / `toolsTotal` 定义处，约 :190-194）
- Modify: `electron-prototype/electron/src/renderer/src/section-icons.ts`（`TOOLBOX_ICONS` 表）
- Test: `electron-prototype/electron/src/renderer/src/__tests__/interactive-tools.spec.ts`

- [ ] **Step 1: 写失败测试**

`electron-prototype/electron/src/renderer/src/__tests__/interactive-tools.spec.ts`：

```ts
// 注册表与工具池合并：交互工具恒置顶、参与收藏过滤；不计入可运行率分母口径。
import { beforeEach, describe, expect, it } from 'vitest'
import {
  catalogToolsTotal,
  examples,
  favOnly,
  toolboxItems,
  toolsTotal
} from '../store/catalog'
import { DATE_CALC_ID, interactiveToolItems, isInteractiveId } from '../interactive-tools'
import { favorites } from '../store/prefs'
import type { VExample } from '../store/catalog'

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
  ] as VExample[]
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
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd electron-prototype/electron && npx vitest run src/__tests__/interactive-tools.spec.ts`
Expected: FAIL（模块不存在 / toolsTotal 仍为 2）。

- [ ] **Step 3: 实现注册表**

`electron-prototype/electron/src/renderer/src/interactive-tools.ts`：

```ts
// interactive-tools.ts：交互工具注册表——不是可运行 Python 示例，是应用内交互页的
// 工具箱门面。不进内置库 JSON（避免污染可运行率 / 守卫 / sidecar 文件装载），
// 由 catalog 合并进工具池：参与搜索与收藏（客户端匹配），恒置顶展示。
import type { VExample } from './store/catalog'

export const INTERACTIVE_PREFIX = 'interactive:'
export const DATE_CALC_ID = `${INTERACTIVE_PREFIX}date-calculator`

export function isInteractiveId(id: string | undefined | null): boolean {
  return !!id && id.startsWith(INTERACTIVE_PREFIX)
}

export const interactiveToolItems: VExample[] = [
  {
    id: DATE_CALC_ID,
    name: 'date-calculator',
    category: 'tools',
    path: '',
    title: '日期计算器',
    description: '任选起止日期，即时计算间隔、正倒计时、日期加减与日历跨度，附等价 Python 代码。',
    tags: ['日期', '交互工具']
  }
]
```

- [ ] **Step 4: 修改 catalog.ts**

在 `store/catalog.ts` 的 import 区加入：

```ts
import { interactiveToolItems } from '../interactive-tools'
```

替换 `toolboxItems` 与 `toolsTotal` 两个 computed（原 :190-194 附近）为：

```ts
export const toolboxItems = computed<VExample[]>(() => {
  const list = FilterEngine.filterExamples(examples.value, toolboxQuery.value, filterContext.value) as VExample[]
  // 交互工具不在 examples 目录池，不走 FilterEngine：客户端匹配搜索词与收藏，恒置顶。
  // 搜索词用 debounce 后的 appliedToolSearch，与目录池口径一致。
  const q = appliedToolSearch.value.trim().toLowerCase()
  const inter = interactiveToolItems.filter((t) => {
    if (favOnly.value && !favorites.value.has(t.id)) return false
    if (q && !`${t.title ?? ''} ${t.description ?? ''} ${(t.tags ?? []).join(' ')}`.toLowerCase().includes(q))
      return false
    return true
  })
  return [...inter, ...list]
})

/** 目录池内工具数：可运行率的分母口径（交互工具无 .py 文件，不计入） */
export const catalogToolsTotal = computed(() => examples.value.filter((e) => e.category === 'tools').length)

/** 工具总数：状态栏 / 导航徽章口径（目录池 + 交互工具） */
export const toolsTotal = computed(() => interactiveToolItems.length + catalogToolsTotal.value)
```

注意：若 `favorites` 尚未被 catalog.ts 导入，从 `./prefs` 补 `favorites`（`filterContext` 已在用它，通常已导入）。

- [ ] **Step 5: 加分组图标**

`src/section-icons.ts` 的 `TOOLBOX_ICONS` 表加一条（lucide 导入区补 `Sparkles`）：

```ts
  interactive: Sparkles,
```

- [ ] **Step 6: 运行测试与 typecheck**

Run: `cd electron-prototype/electron && npx vitest run src/__tests__/interactive-tools.spec.ts && npm run typecheck`
Expected: 测试 PASS；typecheck 无错误（其他引用 toolsTotal 的视图无需改动——它仍是一 number）。

- [ ] **Step 7: Commit**

```bash
git add electron-prototype/electron/src/renderer/src/interactive-tools.ts \
        electron-prototype/electron/src/renderer/src/store/catalog.ts \
        electron-prototype/electron/src/renderer/src/section-icons.ts \
        electron-prototype/electron/src/renderer/src/__tests__/interactive-tools.spec.ts
git commit -m "feat(date-tool): 交互工具注册表并入工具池（置顶/搜索/收藏/计数口径）"
```

---

### Task 5: store/interactive.ts 页面状态

**Files:**
- Create: `electron-prototype/electron/src/renderer/src/store/interactive.ts`

- [ ] **Step 1: 实现**

`electron-prototype/electron/src/renderer/src/store/interactive.ts`：

```ts
// store/interactive.ts：日期计算器页面状态（日期对 / 激活 Tab / 加减行）。
// 会话内记忆：切走再回来保持；返回列表只清 selectedId，不清这里。
import { ref } from 'vue'
import { selectedId } from './detail'
import { DATE_CALC_ID } from '../interactive-tools'

export type TabKey = 'diff' | 'countdown' | 'arith' | 'calendar'

export interface ArithRow {
  target: 'd1' | 'd2'
  op: '+' | '-'
  n: number
  unit: 'day' | 'week' | 'month' | 'year'
}

export const dateA = ref('2024-01-01')
export const dateB = ref('2025-01-01')
export const activeTab = ref<TabKey>('diff')
export const arithRows = ref<ArithRow[]>([{ target: 'd1', op: '+', n: 30, unit: 'day' }])

/** 打开交互工具页（selectedId 命中 interactive: 前缀时 App.vue 渲染专属页） */
export function openInteractive(id: string = DATE_CALC_ID): void {
  selectedId.value = id
}

/** 返回列表（本页无脏状态，直接清选中） */
export function closeInteractive(): void {
  selectedId.value = null
}

export function swapDates(): void {
  const t = dateA.value
  dateA.value = dateB.value
  dateB.value = t
}
```

- [ ] **Step 2: typecheck**

Run: `cd electron-prototype/electron && npm run typecheck`
Expected: 无错误。

- [ ] **Step 3: Commit**

```bash
git add electron-prototype/electron/src/renderer/src/store/interactive.ts
git commit -m "feat(date-tool): 页面状态 store（日期对/Tab/加减行/开关）"
```

---

### Task 6: ExampleCard 交互形态 + ToolboxView 分组置顶

**Files:**
- Modify: `electron-prototype/electron/src/renderer/components/ExampleCard.vue`
- Modify: `electron-prototype/electron/src/renderer/components/ToolboxView.vue`
- Test: `electron-prototype/electron/src/renderer/components/__tests__/date-card.spec.ts`

- [ ] **Step 1: 写失败测试**

`electron-prototype/electron/src/renderer/components/__tests__/date-card.spec.ts`：

```ts
// ExampleCard 交互形态：隐藏运行与质量分，显示「交互」徽章，open 正常发出。
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ExampleCard from '../ExampleCard.vue'
import type { VExample } from '../../src/store/catalog'

const base: VExample = {
  id: 'interactive:date-calculator',
  name: 'date-calculator',
  category: 'tools',
  path: '',
  title: '日期计算器',
  description: '任选起止日期即时计算。'
}

describe('ExampleCard interactive 形态', () => {
  it('不渲染运行按钮，显示交互徽章，点击发 open', async () => {
    const w = mount(ExampleCard, { props: { ex: base, interactive: true } })
    expect(w.find('[data-testid="card-run"]').exists()).toBe(false)
    expect(w.find('[data-testid="interactive-badge"]').exists()).toBe(true)
    await w.trigger('click')
    expect(w.emitted('open')).toHaveLength(1)
  })
  it('普通卡片不受影响（运行按钮仍在）', () => {
    const w = mount(ExampleCard, {
      props: { ex: { ...base, id: 'tools_x', run_status: 'runnable', quality_score: 80 } }
    })
    expect(w.find('[data-testid="card-run"]').exists()).toBe(true)
    expect(w.find('[data-testid="interactive-badge"]').exists()).toBe(false)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/date-card.spec.ts`
Expected: FAIL（无 interactive prop 行为）。

- [ ] **Step 3: 修改 ExampleCard.vue**

1) props 声明改为：

```ts
const props = defineProps<{ ex: VExample; selected?: boolean; faved?: boolean; enterIndex?: number; interactive?: boolean }>()
```

2) 模板行 3（注释锚点「行 3 = 质量分 + 主标签 + 高危 + 运行（安静按钮）+ 状态」所在容器）：
- 质量分与运行按钮两个节点包一层 `<template v-if="!interactive">…</template>`
- 运行按钮加 `data-testid="card-run"`（若尚无）
- 容器内追加交互徽章：

```html
<span v-if="interactive" data-testid="interactive-badge" class="chip-ic" aria-label="交互工具">
  <MousePointerClick :size="13" :stroke-width="1.5" />
</span>
```

3) lucide 导入行补 `MousePointerClick`（`import { MousePointerClick, Play, Star } from 'lucide-vue-next'`）。

- [ ] **Step 4: 修改 ToolboxView.vue**

1) script 导入：

```ts
import { isInteractiveId } from '../src/interactive-tools'
import { openInteractive } from '../src/store/interactive'
```

2) `groups` computed 替换为（原为 `buildToolboxGroups(toolboxItems.value).map(...)` 一行）：

```ts
const groups = computed(() => {
  const all = toolboxItems.value
  const inter = all.filter((t) => isInteractiveId(t.id))
  const rest = buildToolboxGroups(all.filter((t) => !isInteractiveId(t.id))).map((g) => ({
    ...g,
    items: sortVExamples(g.items)
  }))
  return inter.length ? [{ key: 'interactive', label: '交互工具', items: sortVExamples(inter) }, ...rest] : rest
})
```

3) 卡片事件分支（script 中新增，替换模板里的直连）：

```ts
function onOpen(id: string): void {
  if (isInteractiveId(id)) openInteractive(id)
  else void openDetail(id)
}
```

4) 模板 `<ExampleCard>` 节点改为：

```html
<ExampleCard
  v-for="(ex, i) in isExpanded(g.key) ? g.items : g.items.slice(0, PREVIEW_COUNT)"
  :key="ex.id"
  :ex="ex"
  :enter-index="i"
  :faved="isFavorite(ex.id)"
  :interactive="isInteractiveId(ex.id)"
  @open="onOpen(ex.id)"
  @fav="toggleFavorite(ex.id)"
  @run="onRun(ex.id)"
/>
```

- [ ] **Step 5: 运行测试 + 既有卡片测试回归 + typecheck**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/date-card.spec.ts components/__tests__/cards.spec.ts && npm run typecheck`
Expected: 全部 PASS（cards.spec 回归确认普通卡片无行为变化）。

- [ ] **Step 6: Commit**

```bash
git add electron-prototype/electron/src/renderer/components/ExampleCard.vue \
        electron-prototype/electron/src/renderer/components/ToolboxView.vue \
        electron-prototype/electron/src/renderer/components/__tests__/date-card.spec.ts
git commit -m "feat(date-tool): 工具箱交互卡片形态与置顶分组（打开走专属页）"
```

---

### Task 7: sidecar 契约扩展——run_example 可选 code（adhoc 运行）

**Files:**
- Modify: `electron-prototype/shared/protocol.ts:200-205`（`RunExampleParams`）
- Modify: `electron-prototype/electron/src/preload/index.ts:68`（window.sidecar 类型）
- Modify: `electron-prototype/sidecar/server.py`（`method_run_example` 与 `_run_subprocess`）
- Test: `tests/test_guard_protocol.py`

- [ ] **Step 1: 写失败守卫测试**

在 `tests/test_guard_protocol.py` 文件末尾追加（沿用文件内 `_ProtocolEnv` 既有夹具与 G7 的等待模式）：

```python
# ------------------------------------------- 金标：code 覆盖运行（adhoc 工作区，不落真相源）


def test_g9_run_example_code_override_runs_in_adhoc_workspace(tmp_path):
    """可选 code：任意 id + code 在一次性 adhoc 工作区执行；输出照常推送。"""
    with _ProtocolEnv(tmp_path) as env:

        async def scenario() -> dict:
            await server.method_run_example(
                1,
                {"id": "no-such-example", "code": "print('ADHOC_OK')", "timeout": 30},
            )
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if env.finished():
                    return env.finished()[-1]
                await asyncio.sleep(0.05)
            raise AssertionError("run_finished 未到达")

        finished = asyncio.run(scenario())
        assert finished["exit_code"] == 0
        assert "ADHOC_OK" in "".join(env.texts())


def test_g9_code_override_rejects_bad_params(tmp_path):
    """code 非字符串 / 空串 / 超长 → -32602，且不产生运行。"""
    with _ProtocolEnv(tmp_path) as env:

        async def scenario() -> list:
            await server.method_run_example(1, {"id": "x", "code": 123, "timeout": 30})
            await server.method_run_example(2, {"id": "x", "code": "   ", "timeout": 30})
            await server.method_run_example(3, {"id": "x", "code": "x" * 64_001, "timeout": 30})
            await asyncio.sleep(0.2)
            return env.errors()

        errs = asyncio.run(scenario())
        assert len(errs) == 3, f"应恰好 3 个错误响应: {errs}"
        assert all(e["error"]["code"] == -32602 for e in errs)
        assert env.finished() == []
```

若 `_ProtocolEnv` 没有 `errors()` 收集器（先 `grep -n "def errors\|self.errors\|_error" tests/test_guard_protocol.py` 查看），则按该文件已有的错误响应读取方式改写断言；若确实没有错误收集通道，就退而断言「`env.finished()` 为空 + 主进程 stdout 无 run_output」——两种写法都要保证**负例不会静默通过**。

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_guard_protocol.py -k g9 -q`
Expected: FAIL（code 参数被忽略 → `示例不存在: no-such-example` 错误，或 finished 为空）。

- [ ] **Step 3: protocol.ts 与 preload 类型扩展**

`shared/protocol.ts` 的 `RunExampleParams`：

```ts
export interface RunExampleParams {
  id: string
  args?: string[]
  timeout?: number
  /** 可选代码覆盖（交互工具抽屉）：非空字符串 ≤64000 字符，在一次性 adhoc 工作区运行 */
  code?: string
  [key: string]: unknown
}
```

`electron/src/preload/index.ts:68` 的类型声明改为：

```ts
  runExample: (params: { id: string; args?: string[]; timeout?: number; code?: string }) => Promise<{ run_id: string }>
```

（:180 的实现透传 `Record<string, unknown>`，无需改。）

- [ ] **Step 4: server.py — method_run_example 校验与分支**

在 `method_run_example` 中，`args` 校验之后插入：

```python
    # 可选 code 覆盖（交互工具抽屉「运行」）：一次性 adhoc 工作区，不触碰任何真相源
    code = params.get("code")
    if code is not None:
        if not isinstance(code, str) or not code.strip():
            _error(req_id, -32602, "code 必须是非空字符串")
            return
        if len(code) > 64_000:
            _error(req_id, -32602, "code 超长（上限 64000 字符）")
            return
    item = _item_of(example_id)
    if item is None and code is None:
        _error(req_id, -32602, f"示例不存在: {example_id}")
        return
```

（替换原 `item = _item_of(example_id)` + `if item is None: …` 两段；`item` 允许为 None。）

任务创建行改为：

```python
    task = asyncio.create_task(_run_subprocess(run_id, item, args, timeout, adhoc_code=code))
```

- [ ] **Step 5: server.py — _run_subprocess adhoc 分支**

签名改为：

```python
async def _run_subprocess(
    run_id: str,
    item: ExampleItem | None,
    args: list[str],
    timeout: float,
    *,
    adhoc_code: str | None = None,
) -> None:
```

原「确保工作区」块整体替换为：

```python
    if adhoc_code is not None:
        # 一次性临时工作区：不落真相源，随 cache_root 版本目录隔离
        workspace = _ensure_store().workspace_root / "adhoc" / run_id
        workspace.mkdir(parents=True, exist_ok=True)
        file_path = workspace / "main.py"
        file_path.write_text(adhoc_code, encoding="utf-8")
        working_dir = workspace
    else:
        workspace = await asyncio.to_thread(_ensure_store().ensure_workspace, item)
        if workspace is None:
            _notify("run_output", {"run_id": run_id, "text": "[错误] 无法准备工作区，运行已取消\n"})
            _notify("run_finished", {"run_id": run_id, "exit_code": -1})
            return
        file_path = workspace / item.name
        working_dir = workspace
```

`PYTHONPATH` 构建行改为：

```python
    pythonpath_parts = ([] if adhoc_code is not None else _ensure_store().run_pythonpath(item)) + [str(REPO_ROOT)]
```

（其余不动：`find_requirements(file_path)` 对 adhoc 的 main.py 天然无 requirements.txt；`item` 仅在非 adhoc 分支解引用。）

- [ ] **Step 6: 运行守卫测试 + 既有协议守卫回归**

Run: `.venv/bin/python -m pytest tests/test_guard_protocol.py -q`
Expected: 全部 PASS（含原 G7「按 id 寻址、path 不生效」不受影响）。

- [ ] **Step 7: Commit**

```bash
git add electron-prototype/shared/protocol.ts electron-prototype/electron/src/preload/index.ts \
        electron-prototype/sidecar/server.py tests/test_guard_protocol.py
git commit -m "feat(sidecar): run_example 可选 code 参数——一次性 adhoc 工作区运行（守卫 G9）"
```

---

### Task 8: store/date-run.ts 抽屉运行链路（TDD）

**Files:**
- Create: `electron-prototype/electron/src/renderer/src/store/date-run.ts`
- Test: `electron-prototype/electron/src/renderer/src/__tests__/date-run.spec.ts`

- [ ] **Step 1: 写失败测试**

`electron-prototype/electron/src/renderer/src/__tests__/date-run.spec.ts`：

```ts
// date-run：runExample(code) 封装 + run_id 事件过滤。sidecar-client 整体 mock，
// 用捕获的监听器模拟事件流，不依赖 window.sidecar 桩的行为。
import { beforeEach, describe, expect, it, vi } from 'vitest'

const listeners: Record<string, (data: unknown) => void> = {}
const runExample = vi.fn(async () => ({ run_id: 'r1' }))
const stopRun = vi.fn(async () => ({ status: 'terminating' as const, run_id: 'r1' }))

vi.mock('../sidecar-client', () => ({
  api: { runExample: (...a: unknown[]) => runExample(...(a as [])), stopRun: (...a: unknown[]) => stopRun(...(a as [])) },
  on: (ch: string, fn: (data: unknown) => void) => {
    listeners[ch] = fn
    return () => {}
  }
}))

import { runBusy, runExitCode, runOutput, runSnippet, stopSnippet } from '../store/date-run'
import { DATE_CALC_ID } from '../interactive-tools'

beforeEach(() => {
  runOutput.value = ''
  runExitCode.value = null
  runBusy.value = false
  runExample.mockClear()
})

describe('runSnippet', () => {
  it('带 code 调 runExample 并进入 busy', async () => {
    runSnippet(DATE_CALC_ID, "print('hi')")
    await vi.waitFor(() => expect(runExample).toHaveBeenCalledWith(DATE_CALC_ID, "print('hi')"))
    expect(runBusy.value).toBe(true)
  })
  it('runOutput/runFinished 只接受本 run_id', async () => {
    runSnippet(DATE_CALC_ID, "print('hi')")
    await vi.waitFor(() => expect(runBusy.value).toBe(true))
    listeners.runOutput({ run_id: 'other', text: 'NOISE' })
    listeners.runOutput({ run_id: 'r1', text: 'HI\n' })
    expect(runOutput.value).toBe('HI\n')
    listeners.runFinished({ run_id: 'r1', exit_code: 0 })
    expect(runBusy.value).toBe(false)
    expect(runExitCode.value).toBe(0)
  })
  it('runExample 拒绝时落错误文本并退出 busy', async () => {
    runExample.mockRejectedValueOnce(new Error('code 超长（上限 64000 字符）'))
    runSnippet(DATE_CALC_ID, 'x')
    await vi.waitFor(() => expect(runBusy.value).toBe(false))
    expect(runOutput.value).toContain('code 超长')
  })
  it('stopSnippet 调 stopRun', () => {
    runSnippet(DATE_CALC_ID, 'x')
    stopSnippet()
    expect(stopRun).toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd electron-prototype/electron && npx vitest run src/__tests__/date-run.spec.ts`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 date-run.ts**

`electron-prototype/electron/src/renderer/src/store/date-run.ts`：

```ts
// store/date-run.ts：日期计算器抽屉的「运行」链路。
// 走 sidecar run_example 的可选 code 参数（adhoc 工作区），按本页 run_id 过滤事件，
// 与 detail store 的输出面完全独立（不共享 appendOutput / surfaceState）。
import { ref } from 'vue'
import { api, on } from '../sidecar-client'

export const runOutput = ref('')
export const runExitCode = ref<number | null>(null)
export const runBusy = ref(false)

let currentRunId: string | null = null

export function runSnippet(id: string, code: string): void {
  if (runBusy.value) return
  runBusy.value = true
  runOutput.value = ''
  runExitCode.value = null
  api
    .runExample({ id, code })
    .then(({ run_id }) => {
      currentRunId = run_id
    })
    .catch((err) => {
      runBusy.value = false
      currentRunId = null
      runOutput.value = `[错误] ${(err as Error).message}\n`
    })
}

export function stopSnippet(): void {
  if (!currentRunId) return
  void api.stopRun(currentRunId).catch(() => {})
}

on('runOutput', (e) => {
  if (e.run_id === currentRunId) runOutput.value += e.text
})
on('runFinished', (e) => {
  if (e.run_id !== currentRunId) return
  runExitCode.value = e.exit_code
  runBusy.value = false
})
```

- [ ] **Step 4: 运行确认通过 + typecheck**

Run: `cd electron-prototype/electron && npx vitest run src/__tests__/date-run.spec.ts && npm run typecheck`
Expected: PASS / 无错误。

- [ ] **Step 5: Commit**

```bash
git add electron-prototype/electron/src/renderer/src/store/date-run.ts \
        electron-prototype/electron/src/renderer/src/__tests__/date-run.spec.ts
git commit -m "feat(date-tool): 抽屉运行链路（runExample+code，事件按 run_id 过滤）"
```

---

### Task 9: date-calculator 页面组件（输入行 + 四 Tab）

**Files:**
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/DateRangeInputs.vue`
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/TabDiff.vue`
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/TabCountdown.vue`
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/TabArithmetic.vue`
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/TabCalendar.vue`

- [ ] **Step 1: DateRangeInputs.vue**

```vue
<script setup lang="ts">
// DateRangeInputs：全局日期对输入行（四 Tab 共享）。
// 原生 input[type=date]；星期标注随值即时更新；解析失败标红；
// 预设是单日期快捷值，写入最近聚焦的日期框（默认 d1）。
import { computed, ref } from 'vue'
import { ArrowLeftRight } from 'lucide-vue-next'
import { formatYMD, parseDate, todayYMD, weekdayZh } from '../../src/date-core'
import { dateA, dateB, swapDates } from '../../src/store/interactive'
import BaseButton from '../base/BaseButton.vue'

const lastFocused = ref<'a' | 'b'>('a')
const validA = computed(() => !!parseDate(dateA.value))
const validB = computed(() => !!parseDate(dateB.value))
const wdA = computed(() => {
  const v = parseDate(dateA.value)
  return v ? weekdayZh(v) : '无效日期'
})
const wdB = computed(() => {
  const v = parseDate(dateB.value)
  return v ? weekdayZh(v) : '无效日期'
})

const INPUT_CLS =
  'px-2 h-8 bg-page border rounded-control text-ink text-control font-mono outline-none transition-[border-color] dur-fast hover:border-line-strong focus:border-accent'

const PRESETS: Array<{ label: string; value: () => string }> = [
  { label: '今天', value: () => formatYMD(todayYMD()) },
  { label: '今年元旦', value: () => `${todayYMD().y}-01-01` },
  {
    label: '明年今天',
    value: () => {
      const t = todayYMD()
      return `${t.y + 1}-${String(t.m).padStart(2, '0')}-${String(t.d).padStart(2, '0')}`
    }
  },
  { label: '闰年日', value: () => '2024-02-29' }
]

function applyPreset(value: string): void {
  if (lastFocused.value === 'a') dateA.value = value
  else dateB.value = value
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <div class="flex items-center gap-1.5">
      <input
        v-model="dateA"
        type="date"
        data-testid="date-a"
        :class="[INPUT_CLS, validA ? 'border-line' : 'border-danger']"
        aria-label="起始日期"
        @focus="lastFocused = 'a'"
      />
      <span class="text-caption text-ink-mute w-[58px]" data-testid="weekday-a">{{ wdA }}</span>
    </div>
    <BaseButton square title="交换起止日期" aria-label="交换起止日期" @click="swapDates()">
      <ArrowLeftRight :size="14" />
    </BaseButton>
    <div class="flex items-center gap-1.5">
      <input
        v-model="dateB"
        type="date"
        data-testid="date-b"
        :class="[INPUT_CLS, validB ? 'border-line' : 'border-danger']"
        aria-label="结束日期"
        @focus="lastFocused = 'b'"
      />
      <span class="text-caption text-ink-mute w-[58px]" data-testid="weekday-b">{{ wdB }}</span>
    </div>
    <div class="flex gap-1.5 ml-auto">
      <button
        v-for="p in PRESETS"
        :key="p.label"
        class="border border-line rounded-control px-2 h-7 text-caption text-ink-mute hover:text-accent hover:border-accent bg-transparent cursor-pointer transition-colors dur-fast"
        data-testid="dc-preset"
        @click="applyPreset(p.value())"
      >
        {{ p.label }}
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: TabDiff.vue**

```vue
<script setup lang="ts">
// TabDiff：日期差——大数字天数 + 指标行 + 跨度色带（垂直叙事）。
import { computed } from 'vue'
import { diffRange, parseDate } from '../../src/date-core'
import { dateA, dateB } from '../../src/store/interactive'

const result = computed(() => {
  const a = parseDate(dateA.value)
  const b = parseDate(dateB.value)
  if (!a || !b) return null
  return { ...diffRange(a, b), span: `${a.y}年${a.m}月`, spanEnd: `${b.y}年${b.m}月` }
})
</script>

<template>
  <div v-if="!result" class="text-control text-ink-mute pt-10 text-center">请补全两个有效日期</div>
  <div v-else class="flex flex-col gap-5 items-center pt-4 pb-2">
    <div v-if="result.swapped" data-testid="swap-hint" class="text-caption text-warn">
      起点晚于终点，结果按较晚为终点计算
    </div>
    <div class="text-center">
      <div class="font-semibold text-ink leading-none m-0" style="font-size: 44px" data-testid="diff-days">
        {{ result.days }}<span class="text-control text-ink-mute font-normal ml-1">天</span>
      </div>
      <div class="text-control text-ink-mute mt-2" data-testid="diff-metrics">
        ≈ {{ result.weeks }} 周 · {{ result.norm.years }} 年 {{ result.norm.months }} 个月 {{ result.norm.days }} 天 ·
        含 {{ result.leapDays }} 个闰日
      </div>
    </div>
    <div class="flex gap-2 w-full">
      <div class="surface-card flex-1 py-2 text-center text-control" data-testid="weekday-start">
        起点 {{ result.weekday1 }}
      </div>
      <div class="surface-card flex-1 py-2 text-center text-control" data-testid="weekday-end">
        终点 {{ result.weekday2 }}
      </div>
    </div>
    <div class="w-full surface-card p-3">
      <div class="flex justify-between text-caption text-ink-faint mb-1.5">
        <span>{{ result.span }}</span><span>{{ result.spanEnd }}</span>
      </div>
      <div class="h-3 rounded-full overflow-hidden bg-accent/15">
        <div class="h-full w-full rounded-full bg-gradient-to-r from-accent/30 to-accent" />
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: TabCountdown.vue**

```vue
<script setup lang="ts">
// TabCountdown：正倒计时——d1/d2 各自距今天数 + 纪念日前瞻（未来最近 3 个）。
import { computed } from 'vue'
import { daysFromToday, formatYMD, parseDate, todayYMD, upcomingAnniversaries } from '../../src/date-core'
import { dateA, dateB } from '../../src/store/interactive'

const rows = computed(() => {
  const today = todayYMD()
  return (
    [
      { key: 'a', label: '起点', raw: dateA.value },
      { key: 'b', label: '终点', raw: dateB.value }
    ] as const
  ).map((it) => {
    const v = parseDate(it.raw)
    if (!v) return { ...it, date: null, delta: 0, list: [] }
    return {
      ...it,
      date: v,
      delta: daysFromToday(v, today),
      list: upcomingAnniversaries(v, today, 3).map((x) => ({ date: formatYMD(x.date), label: x.label }))
    }
  })
})

function deltaText(n: number): string {
  if (n === 0) return '就是今天'
  return n > 0 ? `还有 ${n} 天` : `已过 ${-n} 天`
}
</script>

<template>
  <div class="grid grid-cols-2 gap-4 pt-4 pb-2">
    <div v-for="r in rows" :key="r.key" class="surface-card p-4" :data-testid="`cd-${r.key}`">
      <div class="text-caption text-ink-mute mb-2">{{ r.label }} · {{ r.raw }}</div>
      <template v-if="r.date">
        <div class="font-semibold text-ink" style="font-size: 30px" data-testid="cd-delta">{{ deltaText(r.delta) }}</div>
        <ul class="mt-3 mb-0 pl-4 list-disc text-control text-ink-dim flex flex-col gap-1">
          <li v-for="m in r.list" :key="m.label">{{ m.date }} · {{ m.label }}</li>
        </ul>
      </template>
      <div v-else class="text-control text-ink-mute">无效日期</div>
    </div>
  </div>
</template>
```

- [ ] **Step 4: TabArithmetic.vue**

```vue
<script setup lang="ts">
// TabArithmetic：日期加减——增减行列表（目标 × 运算 × 数值 × 单位），即时出结果。
import { computed } from 'vue'
import { Trash2, Plus } from 'lucide-vue-next'
import { addToDate, formatYMD, parseDate, weekdayZh } from '../../src/date-core'
import { arithRows, dateA, dateB, type ArithRow } from '../../src/store/interactive'

const UNITS: Array<{ v: ArithRow['unit']; label: string }> = [
  { v: 'day', label: '天' },
  { v: 'week', label: '周' },
  { v: 'month', label: '月' },
  { v: 'year', label: '年' }
]

const results = computed(() =>
  arithRows.value.map((r) => {
    const src = parseDate(r.target === 'd1' ? dateA.value : dateB.value)
    if (!src || !Number.isFinite(r.n)) return null
    const out = addToDate(src, r.op === '+' ? r.n : -r.n, r.unit)
    return `${formatYMD(out)}（${weekdayZh(out)}）`
  })
)

function addRow(): void {
  arithRows.value.push({ target: 'd1', op: '+', n: 7, unit: 'day' })
}
function removeRow(i: number): void {
  arithRows.value.splice(i, 1)
}
</script>

<template>
  <div class="flex flex-col gap-2 pt-4 pb-2">
    <div
      v-for="(r, i) in arithRows"
      :key="i"
      class="flex items-center gap-2 surface-card px-3 py-2"
      :data-testid="`arith-row-${i}`"
    >
      <select v-model="r.target" class="px-2 h-7 bg-page border border-line rounded-control text-control text-ink" :aria-label="`第 ${i + 1} 行目标日期`">
        <option value="d1">起点</option>
        <option value="d2">终点</option>
      </select>
      <select v-model="r.op" class="px-2 h-7 bg-page border border-line rounded-control text-control text-ink" :aria-label="`第 ${i + 1} 行运算`">
        <option value="+">＋</option>
        <option value="-">－</option>
      </select>
      <input
        v-model.number="r.n"
        type="number"
        class="px-2 h-7 w-[90px] bg-page border border-line rounded-control text-ink text-control font-mono outline-none focus:border-accent"
        aria-label="数值"
      />
      <select v-model="r.unit" class="px-2 h-7 bg-page border border-line rounded-control text-control text-ink" :aria-label="`第 ${i + 1} 行单位`">
        <option v-for="u in UNITS" :key="u.v" :value="u.v">{{ u.label }}</option>
      </select>
      <span class="text-ink-mute">→</span>
      <span class="text-control text-ink font-mono" data-testid="arith-result">{{ results[i] ?? '—' }}</span>
      <button
        class="ml-auto border-0 bg-transparent text-ink-faint hover:text-danger cursor-pointer"
        :aria-label="`删除第 ${i + 1} 行`"
        @click="removeRow(i)"
      >
        <Trash2 :size="14" />
      </button>
    </div>
    <button
      class="self-start flex items-center gap-1 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer"
      data-testid="arith-add"
      @click="addRow()"
    >
      <Plus :size="14" /> 增加一行
    </button>
  </div>
</template>
```

- [ ] **Step 5: TabCalendar.vue**

```vue
<script setup lang="ts">
// TabCalendar：双月并排日历——起止高亮 + 区间淡染 + 点击格反向设定（第一次点=起点，
// 第二次点=终点，再点重新开始）。左月游标会话内跟随首次进入时的起点月。
import { computed, ref } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { daysBetween, formatYMD, parseDate } from '../../src/date-core'
import { dateA, dateB } from '../../src/store/interactive'

const WD_HEAD = ['一', '二', '三', '四', '五', '六', '日']

function isLeap(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0
}
function lastDay(y: number, m: number): number {
  return [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
}
function monthAdd(c: { y: number; m: number }, n: number): { y: number; m: number } {
  const total = c.y * 12 + (c.m - 1) + n
  return { y: Math.floor(total / 12), m: (((total % 12) + 12) % 12) + 1 }
}

const a = computed(() => parseDate(dateA.value))
const b = computed(() => parseDate(dateB.value))
const cursor = ref<{ y: number; m: number } | null>(null)
const left = computed(() => cursor.value ?? (a.value ? { y: a.value.y, m: a.value.m } : { y: 2024, m: 1 }))
const right = computed(() => monthAdd(left.value, 1))

const pickStage = ref<0 | 1>(0)
function onPick(ymd: string): void {
  if (pickStage.value === 0) {
    dateA.value = ymd
    pickStage.value = 1
  } else {
    dateB.value = ymd
    pickStage.value = 0
  }
}

interface Cell {
  ymd: string
  d: number
  blank?: boolean
  start?: boolean
  end?: boolean
  between?: boolean
}

function monthCells(c: { y: number; m: number }): Cell[] {
  const first = { y: c.y, m: c.m, d: 1 }
  const lead = (new Date(Date.UTC(c.y, c.m - 1, 1)).getUTCDay() + 6) % 7 // 周一起
  const cells: Cell[] = []
  for (let i = 0; i < lead; i++) cells.push({ ymd: `blank-${c.y}-${c.m}-${i}`, d: 0, blank: true })
  const last = lastDay(c.y, c.m)
  for (let d = 1; d <= last; d++) {
    const ymd = formatYMD({ y: c.y, m: c.m, d })
    const v = parseDate(ymd)!
    cells.push({
      d,
      ymd,
      start: a.value ? daysBetween(a.value, v) === 0 : false,
      end: b.value ? daysBetween(b.value, v) === 0 : false,
      between: a.value && b.value ? daysBetween(a.value, v) > 0 && daysBetween(v, b.value) > 0 : false
    })
  }
  return cells
}

function cellCls(c: Cell): string {
  if (c.blank) return ''
  if (c.start) return 'bg-accent text-page font-semibold rounded'
  if (c.end) return 'border border-accent text-accent font-semibold rounded'
  if (c.between) return 'text-ink-dim bg-accent/10'
  return 'text-ink-dim hover:bg-line cursor-pointer'
}
</script>

<template>
  <div class="pt-4 pb-2">
    <div class="flex items-center gap-2 mb-3">
      <button class="border-0 bg-transparent text-ink-mute hover:text-accent cursor-pointer" aria-label="前翻一月" data-testid="cal-prev" @click="cursor = monthAdd(left, -1)">
        <ChevronLeft :size="16" />
      </button>
      <div class="text-caption text-ink-mute">点击日期格：第一次设起点，第二次设终点（当前：{{ pickStage === 0 ? '设起点' : '设终点' }}）</div>
      <button class="ml-auto border-0 bg-transparent text-ink-mute hover:text-accent cursor-pointer" aria-label="后翻一月" data-testid="cal-next" @click="cursor = monthAdd(left, 1)">
        <ChevronRight :size="16" />
      </button>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="mc in [left, right]" :key="`${mc.y}-${mc.m}`" class="surface-card p-3">
        <div class="text-control text-ink font-medium text-center mb-2">{{ mc.y }} 年 {{ mc.m }} 月</div>
        <div class="grid text-center text-caption text-ink-faint mb-1" style="grid-template-columns: repeat(7, 1fr)">
          <span v-for="w in WD_HEAD" :key="w">{{ w }}</span>
        </div>
        <div class="grid text-center text-control" style="grid-template-columns: repeat(7, 1fr); gap: 2px">
          <span v-for="c in monthCells(mc)" :key="c.ymd" class="py-0.5 text-caption rounded" :class="cellCls(c)" :data-testid="c.blank ? undefined : `cal-${c.ymd}`" @click="!c.blank && onPick(c.ymd)">
            {{ c.blank ? '' : c.d }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
```

注意：TabCalendar 的 import 与 `cellCls` 已是最终形态（无脚手架残片），直接照抄落盘。

- [ ] **Step 6: typecheck**

Run: `cd electron-prototype/electron && npm run typecheck`
Expected: 无错误。

- [ ] **Step 7: Commit**

```bash
git add electron-prototype/electron/src/renderer/components/date-calculator/
git commit -m "feat(date-tool): 页面子组件——输入行/日期差/正倒计时/加减/双月日历"
```

---

### Task 10: CodeDrawer.vue（代码抽屉）

**Files:**
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/CodeDrawer.vue`

- [ ] **Step 1: 实现**

`electron-prototype/electron/src/renderer/components/date-calculator/CodeDrawer.vue`：

```vue
<script setup lang="ts">
// CodeDrawer：Python 代码抽屉——随 Tab 与输入实时生成等价代码；默认折叠。
// 只读 Monaco 用独立实例（不复用 detail 单例组件，避免劫持 registerEditor）；
// 复制 / 运行（sidecar adhoc code）/ 停止，输出就地显示。
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ChevronUp, Copy, Play, Square } from 'lucide-vue-next'
import { applyMonacoTheme, currentMonacoTheme, monaco } from '../../monaco'
import { pushToast } from '../../toast'
import { parseDate } from '../../src/date-core'
import { genArithCode, genCalendarCode, genCountdownCode, genDiffCode } from '../../src/py-codegen'
import { DATE_CALC_ID } from '../../src/interactive-tools'
import { activeTab, arithRows, dateA, dateB } from '../../src/store/interactive'
import { runBusy, runExitCode, runOutput, runSnippet, stopSnippet } from '../../src/store/date-run'
import BaseButton from '../base/BaseButton.vue'

const open = ref(false)

const code = computed(() => {
  const a = parseDate(dateA.value)
  const b = parseDate(dateB.value)
  if (!a || !b) return '# 补全两个有效日期后自动生成代码'
  if (activeTab.value === 'diff') return genDiffCode(a, b)
  if (activeTab.value === 'countdown') return genCountdownCode(a, b)
  if (activeTab.value === 'calendar') return genCalendarCode(a, b)
  return genArithCode(a, b, arithRows.value)
})

const container = ref<HTMLDivElement | null>(null)
let ed: ReturnType<typeof monaco.editor.create> | null = null

function createEditor(): void {
  if (!container.value || ed) return
  applyMonacoTheme()
  ed = monaco.editor.create(container.value, {
    value: code.value,
    language: 'python',
    theme: currentMonacoTheme(),
    readOnly: true,
    fontSize: 12,
    minimap: { enabled: false },
    automaticLayout: true,
    scrollBeyondLastLine: false,
    wordWrap: 'on'
  })
}

function toggle(): void {
  open.value = !open.value
  if (open.value) void nextTick(createEditor)
  else {
    ed?.dispose()
    ed = null
  }
}

watch(code, (v) => ed?.setValue(v))
onBeforeUnmount(() => {
  ed?.dispose()
  ed = null
})

async function copyCode(): Promise<void> {
  try {
    await navigator.clipboard.writeText(code.value)
    pushToast('success', '代码已复制')
  } catch {
    pushToast('error', '复制失败')
  }
}
</script>

<template>
  <div class="flex flex-col">
    <button
      class="flex items-center gap-2 px-8 py-2.5 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer select-none"
      data-testid="drawer-toggle"
      :aria-expanded="open"
      @click="toggle()"
    >
      <ChevronUp :size="14" :style="open ? '' : 'transform: rotate(180deg)'" />
      Python 代码<span class="text-caption text-ink-faint">随当前 Tab 与输入实时生成</span>
    </button>
    <div v-if="open" class="px-8 pb-4 flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <BaseButton data-testid="drawer-copy" title="复制代码" @click="copyCode()">
          <Copy :size="14" />
        </BaseButton>
        <BaseButton variant="primary" data-testid="drawer-run" title="用 Python 真实运行并核对结果" :disabled="runBusy" @click="runSnippet(DATE_CALC_ID, code)">
          <Play :size="14" /> 运行
        </BaseButton>
        <BaseButton v-if="runBusy" data-testid="drawer-stop" title="停止运行" @click="stopSnippet()">
          <Square :size="14" />
        </BaseButton>
        <span v-if="runExitCode !== null" class="text-caption" :class="runExitCode === 0 ? 'text-ink-mute' : 'text-danger'" data-testid="run-exit">
          退出码 {{ runExitCode }}
        </span>
      </div>
      <div ref="container" class="h-[240px] border border-line rounded-control overflow-hidden bg-page" />
      <pre
        v-if="runOutput"
        class="m-0 p-3 max-h-[180px] overflow-auto text-control font-mono bg-page border border-line rounded-control whitespace-pre-wrap"
        data-testid="run-output"
        >{{ runOutput }}</pre
      >
    </div>
  </div>
</template>
```

- [ ] **Step 2: typecheck + lint**

Run: `cd electron-prototype/electron && npm run typecheck && npx eslint components/date-calculator/`
Expected: 无错误。（toast 导入路径核对：`components/date-calculator/CodeDrawer.vue` → renderer 根的 `toast.ts` 是 `../../toast`。）

- [ ] **Step 3: Commit**

```bash
git add electron-prototype/electron/src/renderer/components/date-calculator/CodeDrawer.vue
git commit -m "feat(date-tool): 代码抽屉（只读 Monaco 独立实例 + 复制/运行/输出）"
```

---

### Task 11: DateCalculatorPage 组装 + App.vue 分支

**Files:**
- Create: `electron-prototype/electron/src/renderer/components/date-calculator/DateCalculatorPage.vue`
- Modify: `electron-prototype/electron/src/renderer/App.vue`（`<main>` 视图分支，约 :415-421）
- Test: `electron-prototype/electron/src/renderer/components/__tests__/date-page.spec.ts`

- [ ] **Step 1: 写失败测试**

`electron-prototype/electron/src/renderer/components/__tests__/date-page.spec.ts`：

```ts
// 页面组装：Tab 切换、无效日期引导、返回清 selectedId、自动交换提示。
// store 是模块单例：每个用例前复位（沿用 cards.spec 的纪律）。
import { beforeEach, describe, expect, it } from 'vitest'
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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/date-page.spec.ts`
Expected: FAIL（组件不存在）。

- [ ] **Step 3: 实现 DateCalculatorPage.vue**

```vue
<script setup lang="ts">
// DateCalculatorPage：日期计算器专属页（工具箱交互工具，interactive: 前缀路由）。
// 结构 = 页头 + 全局日期对输入行 + 四 Tab（垂直叙事，v-show 保活=会话内记忆）
//        + 底部折叠代码抽屉。本页无脏状态，返回直接清 selectedId。
import { computed } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import DateRangeInputs from './DateRangeInputs.vue'
import TabDiff from './TabDiff.vue'
import TabCountdown from './TabCountdown.vue'
import TabArithmetic from './TabArithmetic.vue'
import TabCalendar from './TabCalendar.vue'
import CodeDrawer from './CodeDrawer.vue'
import { parseDate } from '../../src/date-core'
import { activeTab, closeInteractive, dateA, dateB, type TabKey } from '../../src/store/interactive'

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'diff', label: '日期差' },
  { key: 'countdown', label: '正倒计时' },
  { key: 'arith', label: '日期加减' },
  { key: 'calendar', label: '日历' }
]

const valid = computed(() => !!parseDate(dateA.value) && !!parseDate(dateB.value))
const TAB_CLS = 'border-0 bg-transparent px-3 py-2 text-control cursor-pointer transition-colors dur-fast'
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <div class="app-drag select-none px-8 pt-7 pb-3 flex items-center gap-3">
      <button
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer p-1.5"
        data-testid="dc-back"
        aria-label="返回工具箱"
        @click="closeInteractive()"
      >
        <ArrowLeft :size="15" />
      </button>
      <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">日期计算器</h1>
      <span class="text-caption text-ink-mute border border-line rounded-control px-2 py-0.5">交互工具</span>
    </div>
    <div class="app-no-drag px-8 pb-3">
      <div class="max-w-[1200px] mx-auto w-full"><DateRangeInputs /></div>
    </div>
    <div class="flex-1 min-h-0 overflow-y-auto app-no-drag">
      <div class="max-w-[1200px] mx-auto px-8">
        <div class="flex gap-1 border-b border-line mb-5">
          <button
            v-for="t in TABS"
            :key="t.key"
            :class="[TAB_CLS, activeTab === t.key ? 'text-ink border-b-2 border-accent font-medium' : 'text-ink-mute hover:text-ink']"
            :data-testid="`tab-${t.key}`"
            @click="activeTab = t.key"
          >
            {{ t.label }}
          </button>
        </div>
        <div v-if="!valid" class="text-control text-ink-mute pt-10 text-center" data-testid="dc-invalid">
          请补全两个有效日期
        </div>
        <template v-else>
          <TabDiff v-show="activeTab === 'diff'" />
          <TabCountdown v-show="activeTab === 'countdown'" />
          <TabArithmetic v-show="activeTab === 'arith'" />
          <TabCalendar v-show="activeTab === 'calendar'" />
        </template>
      </div>
    </div>
    <div class="app-no-drag border-t border-line shrink-0">
      <CodeDrawer />
    </div>
  </section>
</template>
```

- [ ] **Step 4: App.vue 分支**

script 导入区加：

```ts
import DateCalculatorPage from './components/date-calculator/DateCalculatorPage.vue'
import { isInteractiveId } from './src/interactive-tools'
```

`<main>` 内（原 `<DetailPage v-if="selectedId" … />` 一行）替换为：

```html
        <DetailPage v-if="selectedId && !isInteractiveId(selectedId)" class="animate-view-in" />
        <DateCalculatorPage v-else-if="selectedId" class="animate-view-in" />
```

- [ ] **Step 5: 运行测试 + 全组件回归 + typecheck**

Run: `cd electron-prototype/electron && npx vitest run components/__tests__/date-page.spec.ts && npm test && npm run typecheck`
Expected: 新测试 PASS；既有测试无回归；typecheck 无错误。
注意 CodeDrawer 挂载会触发 `../../monaco` 导入——若 jsdom 下报错，在 `date-page.spec.ts` 顶部加：

```ts
vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))
```

（记得 `import { vi } from 'vitest'`，并把 `vi.mock` 提到任何 store import 之前——vitest 会提升，但保持书写顺序一致。）

- [ ] **Step 6: 手工冒烟（真实应用）**

Run: `cd electron-prototype/electron && npm run dev`
在应用里验证：工具箱顶部出现「交互工具」分组 → 点开卡片进专属页 → 四 Tab 切换、改日期即时刷新、点日历格设起止、抽屉展开、复制、运行（输出出现 `间隔 366 天` 一类真实输出）、返回回工具箱。视觉走查 theme tokens 无突兀。

- [ ] **Step 7: Commit**

```bash
git add electron-prototype/electron/src/renderer/components/date-calculator/DateCalculatorPage.vue \
        electron-prototype/electron/src/renderer/App.vue \
        electron-prototype/electron/src/renderer/components/__tests__/date-page.spec.ts
git commit -m "feat(date-tool): 专属页组装 + App 路由分支（interactive: 前缀）"
```

---

### Task 12: 5 个变体退役（生成器 + 重生成管线）

**Files:**
- Modify: `scripts/gen_bulk_examples.py`（约 :1026-1036，`add("basics-date-diff", …)` 整块）
- Regenerate: `json_examples/bulk_basics.json`、删除 `json_examples/bulk_basics/basics-date-diff_{1..5}.py`

- [ ] **Step 1: 删除生成器模板**

删除 `gen_bulk_examples.py` 中从 `add("basics-date-diff", "日期计算", …)` 起到该 `add(...)` 调用闭合 `])` 的整块（约 11 行，含 5 个变体参数元组）。

- [ ] **Step 2: 全量重生成（生成器 → 迁移 → 烘焙 → 校验）**

```bash
cd /Users/xiaoye/Desktop/publish/PyCase
.venv/bin/python scripts/gen_bulk_examples.py
.venv/bin/python -m app.migration_cli --dry-run   # 预览：应只有 bulk_basics 相关 create/原位
.venv/bin/python -m app.migration_cli
rm json_examples/bulk_basics/basics-date-diff_*.py
.venv/bin/python -m app.facts_cli bake
.venv/bin/python -m app.facts_cli check
```

Expected: 生成器输出 `基础/算法/工具: 94 条`；migration dry-run 无意外集合变动；`facts_cli check` 报一致。
（若 `.venv/bin/python` 不存在，用 `python3`。）

- [ ] **Step 3: 核对变更范围**

Run: `git status --short json_examples | head -20 && python3 -c "import json; d=json.load(open('json_examples/bulk_basics.json')); print(len(d['examples']))"`
Expected: 改动只落在 `bulk_basics.json` 与 `bulk_basics/` 目录（其余 bulk_* 集合零漂移；若出现大规模无关改写，停下来查生成器确定性，不要硬提交）；计数 `94`。

- [ ] **Step 4: Python 全量测试**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: 全绿（`test_placeholder_corruption.py` / `test_guard_data.py` 等守卫不受影响——它们按树扫描，不钉 99 计数；`test_regression_smoke.py` 的 99 是合成夹具，与库无关）。

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(data): 5 个日期静态变体退役——升级为工具箱交互式日期计算器（99→94）"
```

---

### Task 13: 全局门禁与收尾

- [ ] **Step 1: 渲染层门禁**

```bash
cd electron-prototype/electron
npm run lint
npm run format:check
npm run typecheck
npm test
```
Expected: 全绿。`format:check` 失败就跑 `npm run format` 后复查 diff 再提交。

- [ ] **Step 2: Python 门禁**

```bash
cd /Users/xiaoye/Desktop/publish/PyCase
.venv/bin/python -m pytest tests/ -q
```
Expected: 全绿。

- [ ] **Step 3: 应用冒烟**

```bash
cd electron-prototype/electron && npm run smoke
```
Expected: 构建成功、应用可启动无渲染层报错。

- [ ] **Step 4: 收尾提交（如有 format 产物）**

```bash
git add -A && git commit -m "style: date-tool 门禁格式化产物" || true
```

---

## 计划自审记录（写完即查）

1. **规格覆盖**：§3 入口/路由 → Task 4/6/11；§4 计算核心+对拍 → Task 1/2；§5.1 布局 → Task 9/11；§5.2 四 Tab → Task 9；§5.3 代码抽屉+运行 → Task 3/7/8/10；§6 组件与数据流 → 全部；§7 退役 → Task 12；§8 错误处理 → 输入标红+引导文案（Task 9）、sidecar 失败落错误文本（Task 8）；§9 门禁 → 各任务内 + Task 13；§10 YAGNI 未引入。**无缺口。**
2. **占位符扫描**：TabCalendar 的 import 行含脚手架残片，已在 Step 5 内给出最终行与删除指令——执行时按最终行落盘。其余步骤均为完整代码/命令。
3. **类型一致性**：`ArithRow`（store/interactive）↔ `ArithRowLike`（py-codegen）字段同名同型；`addToDate(v, n, unit)` 签名两处调用一致；`runSnippet(id, code)` 与 `api.runExample({id, code})`（Task 7 扩展后）一致；`isInteractiveId` 被 catalog/ToolboxView/App 三处共用同一导出。
