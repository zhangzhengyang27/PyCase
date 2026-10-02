// tool-schemas-devtools.ts：W3 九个 devtools 交互工具（A-2 组，与原 CLI 条目并存不退役）。
// 只依赖 interactive-tools 的类型（type-only，运行时零导入——与注册表不成环）。
// 口径以 tool-golden.json 为双端唯一事实（Python 参考实现：tests/test_tool_golden.py）；
// JS/Python 方言差异（正则语法、JSON 数字格式化）在各工具描述与黄金用例中显式声明。
import type { FieldValue, InteractiveToolSchema } from './interactive-tools'

const INVALID_CODE = '# 补全输入后自动生成代码'
const str = (v: FieldValue): string => String(v ?? '')

// ---------------------------------------------------------------------------
// 1. 正则测试器（JS RegExp 语义；描述声明与 Python re 的方言差异）
// ---------------------------------------------------------------------------
export const regexTesterSchema: InteractiveToolSchema = {
  id: 'interactive:regex-tester',
  title: '正则测试器',
  description:
    'JS RegExp 语义：分组捕获、偏移定位。与 Python re 存在方言差异（lookbehind 等），复杂语法请用「运行」在真实 Python 里验证。',
  tags: ['正则'],
  fields: [
    { key: 'pattern', label: '正则表达式', type: 'text', required: true, placeholder: '([a-z]+)-([a-z0-9]+)' },
    { key: 'g', label: 'g', type: 'checkbox', default: true, help: '全局（否则只取首个匹配）' },
    { key: 'i', label: 'i', type: 'checkbox', help: '忽略大小写' },
    { key: 'm', label: 'm', type: 'checkbox', help: '多行模式' },
    { key: 's', label: 's', type: 'checkbox', help: '点号匹配换行' },
    { key: 'sample', label: '样本文本', type: 'textarea', required: true, placeholder: '要匹配的文本…' }
  ],
  compute: (v) => {
    const pattern = str(v.pattern)
    const sample = str(v.sample)
    if (!pattern || !sample) return { error: '请补全正则与样本文本' }
    const flags = (['g', 'i', 'm', 's'] as const).filter((f) => v[f] === true).join('')
    let re: RegExp
    try {
      re = new RegExp(pattern, flags)
    } catch (e) {
      return { error: `非法正则：${(e as Error).message}` }
    }
    const items: string[] = []
    const push = (m: RegExpExecArray): void => {
      const span = `[${m.index}-${m.index + m[0].length - 1}]`
      const groups = m
        .slice(1)
        .map((g, i) => `${i + 1}=${g ?? '—'}`)
        .join(', ')
      items.push(groups ? `${span} ${m[0]} → ${groups}` : `${span} ${m[0]}`)
    }
    if (re.global) {
      for (const m of sample.matchAll(re)) push(m as RegExpExecArray)
    } else {
      const m = re.exec(sample)
      if (m) push(m)
    }
    return { primary: { value: String(items.length), unit: '处匹配' }, list: items }
  },
  pyCode: (v) => {
    const pattern = str(v.pattern)
    const sample = str(v.sample)
    if (!pattern || !sample) return INVALID_CODE
    const pyFlags = (['i', 'm', 's'] as const)
      .filter((f) => v[f] === true)
      .map((f) => ({ i: 're.I', m: 're.M', s: 're.S' })[f])
    const global = v.g === true
    return `"""正则测试（re 方言；与 JS 方言差异以描述为准）。"""
import re

pattern = r'''${pattern}'''
text = ${JSON.stringify(sample)}
flags = ${pyFlags.length ? pyFlags.join(' | ') : '0'}
matches = list(re.finditer(pattern, text, flags))${global ? '' : '[:1]'}
for m in matches:
    groups = ", ".join(f"{i}={g}" for i, g in enumerate(m.groups(), 1) if g is not None)
    tail = f" → {groups}" if groups else ""
    print(f"[{m.start()}-{m.end() - 1}] {m.group(0)}{tail}")
print(f"共 {len(matches)} 处")
`
  }
}

// ---------------------------------------------------------------------------
// 2. JSON 格式化校验
// ---------------------------------------------------------------------------
export const jsonFormatSchema: InteractiveToolSchema = {
  id: 'interactive:json-format',
  title: 'JSON 格式化',
  description: '格式化 / 压缩 / 校验三合一。数字格式与 Python json 模块存在浮点表示差异（如 1.0），黄金用例不含浮点。',
  tags: ['JSON'],
  fields: [
    { key: 'input', label: 'JSON 输入', type: 'textarea', required: true, placeholder: '{"a":1}' },
    {
      key: 'indent',
      label: '缩进',
      type: 'select',
      default: '2',
      width: 'half',
      options: [
        { value: '2', label: '2 空格' },
        { value: '4', label: '4 空格' },
        { value: 'compact', label: '压缩' }
      ]
    }
  ],
  compute: (v) => {
    const input = str(v.input)
    if (!input.trim()) return { error: '请输入 JSON' }
    let obj: unknown
    try {
      obj = JSON.parse(input)
    } catch (e) {
      return { error: `JSON 解析失败：${(e as Error).message}` }
    }
    const indent = str(v.indent ?? '2')
    return { text: indent === 'compact' ? JSON.stringify(obj) : JSON.stringify(obj, null, Number(indent)) }
  },
  pyCode: (v) => {
    const input = str(v.input)
    if (!input.trim()) return INVALID_CODE
    const indent = str(v.indent ?? '2')
    const kw = indent === 'compact' ? "separators=(',', ':')" : `indent=${indent === '4' ? '4' : '2'}`
    return `"""JSON 格式化（ensure_ascii=False 对齐 JS 不转义非 ASCII）。"""
import json

data = json.loads(${JSON.stringify(input)})
print(json.dumps(data, ensure_ascii=False, ${kw}))
`
  }
}

// ---------------------------------------------------------------------------
// 3. JSON → dataclass（类型推断规则钉在黄金用例）
// ---------------------------------------------------------------------------
const cap = (s: string): string => (s ? s[0]!.toUpperCase() + s.slice(1) : s)

function pyType(v: unknown): string {
  if (typeof v === 'boolean') return 'bool'
  if (typeof v === 'number') return Number.isInteger(v) ? 'int' : 'float'
  if (typeof v === 'string') return 'str'
  if (Array.isArray(v)) return v.length ? `list[${pyType(v[0])}]` : 'list'
  if (v === null) return 'Any'
  return 'object'
}

function genDataclass(name: string, obj: Record<string, unknown>, lines: string[]): string {
  const fields: Array<[string, string]> = []
  for (const [k, val] of Object.entries(obj)) {
    if (val !== null && typeof val === 'object' && !Array.isArray(val)) {
      const sub = genDataclass(cap(k), val as Record<string, unknown>, lines)
      fields.push([k, sub])
    } else if (Array.isArray(val) && val.length && val[0] !== null && typeof val[0] === 'object') {
      const sub = genDataclass(cap(k) + 'Item', val[0] as Record<string, unknown>, lines)
      fields.push([k, `list[${sub}]`])
    } else {
      fields.push([k, pyType(val)])
    }
  }
  lines.push('@dataclass', `class ${name}:`)
  if (!fields.length) lines.push('    pass')
  for (const [k, t] of fields) lines.push(`    ${k}: ${t}`)
  lines.push('')
  return name
}

export const jsonToDataclassSchema: InteractiveToolSchema = {
  id: 'interactive:json-dataclass',
  title: 'JSON → dataclass',
  description:
    '由 JSON 样本推断 dataclass 定义：嵌套对象生成依赖序子类、对象数组取首元素推断、null → Any。键名需为合法标识符。',
  tags: ['JSON', '代码生成'],
  fields: [
    { key: 'input', label: 'JSON 样本', type: 'textarea', required: true, placeholder: '{"name": "张三"}' },
    { key: 'className', label: '类名', type: 'text', default: 'Sample', width: 'half' }
  ],
  compute: (v) => {
    const input = str(v.input)
    if (!input.trim()) return { error: '请输入 JSON 样本' }
    let obj: unknown
    try {
      obj = JSON.parse(input)
    } catch (e) {
      return { error: `JSON 解析失败：${(e as Error).message}` }
    }
    if (obj === null || typeof obj !== 'object' || Array.isArray(obj)) return { error: '顶层需为 JSON 对象' }
    const name = str(v.className || 'Sample')
    const lines = ['from dataclasses import dataclass', 'from typing import Any', '']
    genDataclass(name, obj as Record<string, unknown>, lines)
    return { text: lines.join('\n').replace(/\s+$/, '') + '\n' }
  },
  pyCode: (v) => {
    const r = jsonToDataclassSchema.compute!(v)
    if (r.error) return INVALID_CODE
    return r.text!
  }
}

// ---------------------------------------------------------------------------
// 4. CSV ↔ JSON（RFC 4180：引号转义；单元格类型推断 int/float/bool/null/str）
// ---------------------------------------------------------------------------
export function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let cur = ''
  let inQ = false
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]!
    if (inQ) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          cur += '"'
          i++
        } else inQ = false
      } else cur += ch
    } else if (ch === '"') inQ = true
    else if (ch === ',') {
      row.push(cur)
      cur = ''
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++
      row.push(cur)
      cur = ''
      if (row.length > 1 || row[0] !== '') rows.push(row)
      row = []
    } else cur += ch
  }
  if (cur !== '' || row.length) {
    row.push(cur)
    if (row.length > 1 || row[0] !== '') rows.push(row)
  }
  return rows
}

function csvCell(v: string): string | number | boolean | null {
  if (v === '') return null
  if (v === 'true') return true
  if (v === 'false') return false
  if (/^-?\d+$/.test(v)) return Number(v)
  if (/^-?\d+\.\d+$/.test(v)) return Number(v)
  return v
}

function csvEscape(v: unknown): string {
  const s = v === null || v === undefined ? '' : String(v)
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export const csvJsonSchema: InteractiveToolSchema = {
  id: 'interactive:csv-json',
  title: 'CSV ↔ JSON 互转',
  description: 'RFC 4180 引号转义双向转换；CSV→JSON 带类型推断（int/float/bool/空→null）。',
  tags: ['CSV', 'JSON'],
  fields: [
    {
      key: 'direction',
      label: '方向',
      type: 'select',
      default: 'csv2json',
      width: 'half',
      options: [
        { value: 'csv2json', label: 'CSV → JSON' },
        { value: 'json2csv', label: 'JSON → CSV' }
      ]
    },
    { key: 'input', label: '输入', type: 'textarea', required: true, placeholder: 'CSV 或 JSON 数组…' }
  ],
  compute: (v) => {
    const input = str(v.input)
    if (!input.trim()) return { error: '请输入内容' }
    if (str(v.direction ?? 'csv2json') === 'csv2json') {
      const rows = parseCsv(input)
      if (rows.length < 1) return { error: 'CSV 为空' }
      const [head, ...body] = rows
      const objs = body.map((r) => Object.fromEntries(head!.map((h, i) => [h, csvCell(r[i] ?? '')])))
      return { text: JSON.stringify(objs, null, 2) }
    }
    let arr: unknown
    try {
      arr = JSON.parse(input)
    } catch (e) {
      return { error: `JSON 解析失败：${(e as Error).message}` }
    }
    if (!Array.isArray(arr) || !arr.length) return { error: '顶层需为非空 JSON 数组' }
    const keys: string[] = []
    for (const o of arr as Record<string, unknown>[]) {
      for (const k of Object.keys(o ?? {})) if (!keys.includes(k)) keys.push(k)
    }
    const text = [
      keys.join(','),
      ...(arr as Record<string, unknown>[]).map((o) => keys.map((k) => csvEscape(o?.[k])).join(','))
    ]
    return { text: text.join('\n') }
  },
  pyCode: (v) => {
    const input = str(v.input)
    if (!input.trim()) return INVALID_CODE
    if (str(v.direction ?? 'csv2json') === 'csv2json') {
      return `"""CSV → JSON（csv 模块按 RFC 4180 解析）。"""
import csv, json

rows = list(csv.reader(${JSON.stringify(input)}.splitlines()))
head, body = rows[0], rows[1:]
print(json.dumps([dict(zip(head, r)) for r in body], ensure_ascii=False, indent=2))
`
    }
    return `"""JSON → CSV（csv 模块写出，自动引号转义）。"""
import csv, io, json

data = json.loads(${JSON.stringify(input)})
keys = list(dict.fromkeys(k for o in data for k in o))
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=keys)
w.writeheader()
w.writerows(data)
print(buf.getvalue().rstrip("\\n"))
`
  }
}

// ---------------------------------------------------------------------------
// 5. 时间戳转换器（UTC 口径钉黄金；本地时间行展示不钉——时区相关）
// ---------------------------------------------------------------------------
const p2 = (n: number): string => String(n).padStart(2, '0')

export const timestampSchema: InteractiveToolSchema = {
  id: 'interactive:timestamp',
  title: '时间戳转换',
  description: '秒/毫秒时间戳 ↔ 日期时间双向转换；UTC 口径（黄金用例时区无关），本地时间行按运行环境时区展示。',
  tags: ['时间'],
  fields: [
    {
      key: 'mode',
      label: '方向',
      type: 'select',
      default: 'ts2date',
      width: 'half',
      options: [
        { value: 'ts2date', label: '时间戳 → 日期' },
        { value: 'date2ts', label: '日期 → 时间戳' }
      ]
    },
    {
      key: 'unit',
      label: '单位（时间戳方向）',
      type: 'select',
      default: 's',
      width: 'half',
      options: [
        { value: 's', label: '秒' },
        { value: 'ms', label: '毫秒' }
      ]
    },
    { key: 'value', label: '输入', type: 'text', required: true, placeholder: '1790985600 或 2026-10-03 00:00:00' }
  ],
  compute: (v) => {
    const value = str(v.value).trim()
    if (!value) return { error: '请输入时间戳或日期' }
    if (str(v.mode ?? 'ts2date') === 'ts2date') {
      const raw = Number(value)
      if (!Number.isFinite(raw)) return { error: '时间戳需为数字' }
      const ms = str(v.unit ?? 's') === 'ms' ? raw : raw * 1000
      const d = new Date(ms)
      if (Number.isNaN(d.getTime())) return { error: '时间戳超出范围' }
      const iso = d.toISOString().replace(/\.\d{3}Z$/, 'Z')
      const local = `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())} ${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())}`
      return {
        rows: [
          { label: 'UTC', value: `${iso.slice(0, 19).replace('T', ' ')} UTC`, copy: true },
          { label: 'ISO 8601', value: iso, copy: true },
          { label: '本地时区', value: local, copy: true }
        ]
      }
    }
    const m = /^(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2})(?::(\d{2}))?)?$/.exec(value)
    if (!m) return { error: '无法识别的日期（按 UTC 解析：YYYY-MM-DD[ HH:mm[:ss]]）' }
    const ms = Date.UTC(
      Number(m[1]),
      Number(m[2]) - 1,
      Number(m[3]),
      Number(m[4] ?? 0),
      Number(m[5] ?? 0),
      Number(m[7] ?? 0)
    )
    return {
      rows: [
        { label: '秒', value: String(Math.floor(ms / 1000)), copy: true },
        { label: '毫秒', value: String(ms), copy: true }
      ]
    }
  },
  pyCode: (v) => {
    const value = str(v.value).trim()
    if (!value) return INVALID_CODE
    if (str(v.mode ?? 'ts2date') === 'ts2date') {
      const div = str(v.unit ?? 's') === 'ms' ? '1000' : '1'
      return `"""时间戳 → UTC 日期。"""
from datetime import datetime, timezone

d = datetime.fromtimestamp(int("${value}") / ${div}, tz=timezone.utc)
print(d.strftime("%Y-%m-%d %H:%M:%S"), "UTC")
print(d.strftime("%Y-%m-%dT%H:%M:%SZ"))
`
    }
    return `"""日期 → 时间戳（按 UTC 解析，多格式回退对齐页面口径）。"""
from datetime import datetime, timezone

d = None
for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
    try:
        d = datetime.strptime("${value}", f).replace(tzinfo=timezone.utc)
        break
    except ValueError:
        continue
print(int(d.timestamp()))
`
  }
}

// ---------------------------------------------------------------------------
// 6. UUID / 短 ID 生成器（随机型：黄金只钉格式与唯一性）
// ---------------------------------------------------------------------------
function randomBytes(n: number): Uint8Array {
  const b = new Uint8Array(n)
  globalThis.crypto.getRandomValues(b)
  return b
}

function uuid4(): string {
  const b = randomBytes(16)
  b[6] = (b[6]! & 0x0f) | 0x40
  b[8] = (b[8]! & 0x3f) | 0x80
  const hex = [...b].map((x) => x.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

const B64URL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-'

export const uuidSchema: InteractiveToolSchema = {
  id: 'interactive:uuid',
  title: 'UUID / 短 ID 生成',
  description: 'UUID v4（crypto.getRandomValues，RFC 4122 版本位/变体位正确）与 11 字符 base64url 短 ID。',
  tags: ['生成器'],
  fields: [
    {
      key: 'mode',
      label: '模式',
      type: 'select',
      default: 'uuid4',
      width: 'half',
      options: [
        { value: 'uuid4', label: 'UUID v4' },
        { value: 'short', label: '短 ID（11 位）' }
      ]
    },
    { key: 'count', label: '数量', type: 'number', default: 5, width: 'half' },
    { key: 'upper', label: '大写', type: 'checkbox', help: '仅 UUID 模式生效' }
  ],
  compute: (v) => {
    const raw = Math.trunc(Number(v.count ?? 5))
    if (!Number.isFinite(raw) || raw < 1 || raw > 50) return { error: '数量需为 1~50 的整数' }
    const n = Math.min(Math.max(raw, 1), 50)
    const ids =
      str(v.mode ?? 'uuid4') === 'short'
        ? Array.from({ length: n }, () => [...randomBytes(11)].map((b) => B64URL[b & 63]).join(''))
        : Array.from({ length: n }, uuid4).map((u) => (v.upper === true ? u.toUpperCase() : u))
    return { list: ids }
  },
  pyCode: (v) => {
    const raw = Math.trunc(Number(v.count ?? 5))
    if (!Number.isFinite(raw) || raw < 1 || raw > 50) return INVALID_CODE
    if (str(v.mode ?? 'uuid4') === 'short') {
      return `"""短 ID ×${Math.min(Math.max(raw, 1), 50)}（secrets + base64url）。"""
import base64, secrets

for _ in range(${Math.min(Math.max(raw, 1), 50)}):
    print(base64.urlsafe_b64encode(secrets.token_bytes(9)).rstrip(b"=").decode())
`
    }
    return `"""UUID v4 ×${Math.min(Math.max(raw, 1), 50)}。"""
import uuid

for _ in range(${Math.min(Math.max(raw, 1), 50)}):
    print(str(uuid.uuid4())${v.upper === true ? '.upper()' : ''})
`
  }
}

// ---------------------------------------------------------------------------
// 7. 颜色转换器（HEX / RGB / HSL 互转；舍入口径与 Python colorsys 对拍）
// ---------------------------------------------------------------------------
function hlsToRgb(h: number, l: number, s: number): [number, number, number] {
  if (s === 0) return [l, l, l]
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s
  const p = 2 * l - q
  const hue = (t: number): number => {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1 / 6) return p + (q - p) * 6 * t
    if (t < 1 / 2) return q
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
    return p
  }
  return [hue(h + 1 / 3), hue(h), hue(h - 1 / 3)]
}

function rgbToHls(r: number, g: number, b: number): [number, number, number] {
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2
  if (max === min) return [0, l, 0]
  const d = max - min
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
  let h: number
  if (max === r) h = (g - b) / d + (g < b ? 6 : 0)
  else if (max === g) h = (b - r) / d + 2
  else h = (r - g) / d + 4
  return [h / 6, l, s]
}

export const colorSchema: InteractiveToolSchema = {
  id: 'interactive:color',
  title: '颜色转换器',
  description: '#hex / rgb() / hsl() 三格式互转；HSL 舍入到整数度/百分比，与 Python colorsys 口径对拍。',
  tags: ['前端'],
  fields: [
    {
      key: 'value',
      label: '颜色',
      type: 'text',
      required: true,
      placeholder: '#ff0000 / rgb(255,0,0) / hsl(0,100%,50%)'
    }
  ],
  compute: (v) => {
    const s = str(v.value).trim().toLowerCase()
    if (!s) return { error: '请输入颜色' }
    let r: number, g: number, b: number
    let m = /^#?([0-9a-f]{6})$/.exec(s)
    if (m) {
      r = parseInt(m[1]!.slice(0, 2), 16)
      g = parseInt(m[1]!.slice(2, 4), 16)
      b = parseInt(m[1]!.slice(4, 6), 16)
    } else if ((m = /^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/.exec(s))) {
      r = Number(m[1])
      g = Number(m[2])
      b = Number(m[3])
      if (r > 255 || g > 255 || b > 255) return { error: 'RGB 分量需在 0~255' }
    } else if ((m = /^hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)$/.exec(s))) {
      ;[r, g, b] = hlsToRgb(Number(m[1]) / 360, Number(m[3]) / 100, Number(m[2]) / 100).map((x) => Math.round(x * 255))
    } else {
      return { error: '无法识别的颜色（支持 #hex / rgb() / hsl()）' }
    }
    const [h, l, sl] = rgbToHls(r / 255, g / 255, b / 255)
    return {
      rows: [
        { label: 'HEX', value: `#${[r, g, b].map((x) => x.toString(16).padStart(2, '0')).join('')}`, copy: true },
        { label: 'RGB', value: `rgb(${r}, ${g}, ${b})`, copy: true },
        {
          label: 'HSL',
          value: `hsl(${Math.round(h * 360)}, ${Math.round(sl * 100)}%, ${Math.round(l * 100)}%)`,
          copy: true
        }
      ]
    }
  },
  pyCode: (v) => {
    const s = str(v.value).trim()
    if (!s) return INVALID_CODE
    return `"""颜色三格式互转（colorsys 的 HLS 语义，0~1 浮点区间）。"""
import colorsys

s = "${str(v.value).trim().toLowerCase()}"
# 解析省略：黄金用例已钉三入口；此处以 hex 入口演示
r, g, b = (int(s.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
h, l, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
print(f"#{r:02x}{g:02x}{b:02x}", f"rgb({r}, {g}, {b})",
      f"hsl({round(h * 360)}, {round(ss * 100)}%, {round(l * 100)}%)")
`
  }
}

// ---------------------------------------------------------------------------
// 8. 科学单位换算（系数表与 Python 参考实现共享同一份黄金口径）
// ---------------------------------------------------------------------------
const UNIT_FACTORS: Record<string, Record<string, number>> = {
  长度: { m: 1, km: 1000, cm: 0.01, mi: 1609.344, ft: 0.3048, in: 0.0254, nmi: 1852 },
  质量: { kg: 1, g: 0.001, t: 1000, lb: 0.45359237, oz: 0.028349523125 },
  数据: { B: 1, KiB: 1024, MiB: 1048576, GiB: 1073741824 }
}

function unitOptions(dim: string) {
  return Object.keys(UNIT_FACTORS[dim] ?? {}).map((u) => ({ value: u, label: u }))
}

export const unitConvertSchema: InteractiveToolSchema = {
  id: 'interactive:unit-convert',
  title: '科学单位换算',
  description: '长度 / 质量 / 数据（二进制）三量纲；系数口径与黄金用例一致，结果保留 6 位有效小数并去尾零。',
  tags: ['换算'],
  fields: [
    {
      key: 'dim',
      label: '量纲',
      type: 'select',
      default: '长度',
      width: 'half',
      options: Object.keys(UNIT_FACTORS).map((k) => ({ value: k, label: k }))
    },
    { key: 'value', label: '数值', type: 'text', required: true, placeholder: '5', width: 'half' },
    {
      key: 'from',
      label: '源单位',
      type: 'select',
      default: 'km',
      width: 'half',
      options: (v) => unitOptions(str(v.dim ?? '长度'))
    },
    {
      key: 'to',
      label: '目标单位',
      type: 'select',
      default: 'mi',
      width: 'half',
      options: (v) => unitOptions(str(v.dim ?? '长度'))
    }
  ],
  compute: (v) => {
    const dim = str(v.dim ?? '长度')
    const factors = UNIT_FACTORS[dim]
    if (!factors) return { error: '未知量纲' }
    const n = Number(v.value)
    if (v.value === undefined || v.value === '' || !Number.isFinite(n)) return { error: '请输入数值' }
    const frm = str(v.from)
    const to = str(v.to)
    if (!factors[frm] || !factors[to]) return { error: '未知单位' }
    const out = (n * factors[frm]) / factors[to]
    return {
      primary: { value: out.toFixed(6).replace(/0+$/, '').replace(/\.$/, ''), unit: to },
      rows: [
        { label: `${n} ${frm} =`, value: `${out.toFixed(6).replace(/0+$/, '').replace(/\.$/, '')} ${to}`, copy: true }
      ]
    }
  },
  pyCode: (v) => {
    const dim = str(v.dim ?? '长度')
    const n = Number(v.value)
    const factors = UNIT_FACTORS[dim]
    if (!factors || v.value === undefined || v.value === '' || !Number.isFinite(n)) return INVALID_CODE
    const frm = str(v.from)
    const to = str(v.to)
    if (!factors[frm] || !factors[to]) return INVALID_CODE
    return `"""单位换算：${dim}（系数表口径与页面一致）。"""
FACTORS = ${JSON.stringify(factors)}
n = ${n}
out = n * FACTORS["${frm}"] / FACTORS["${to}"]
print(f"{out:.6f}".rstrip("0").rstrip("."))
`
  }
}

// ---------------------------------------------------------------------------
// 9. 密码强度检查（评分规则钉在黄金用例：长度阶梯 + 字符类 + 常见口令/重复/顺序惩罚）
// ---------------------------------------------------------------------------
const COMMON_PWDS = ['123456', 'password', 'qwerty', '12345678', '111111', '123456789', 'abc123', 'password1']

export const pwdStrengthSchema: InteractiveToolSchema = {
  id: 'interactive:pwd-strength',
  title: '密码强度检查',
  description:
    '评分口径：长度阶梯（6/8/12/16 → 最多 40）+ 字符类（小/大/数字 10、符号 15）− 常见弱口令 20 − 单字符重复 15 − 顺序序列 10，0~100 截断。',
  tags: ['安全'],
  fields: [{ key: 'value', label: '密码', type: 'text', required: true, placeholder: '输入要评估的密码（不会外发）' }],
  compute: (v) => {
    const p = str(v.value)
    if (!p) return { error: '请输入密码' }
    let score = 0
    if (p.length >= 6) score += 10
    if (p.length >= 8) score += 10
    if (p.length >= 12) score += 10
    if (p.length >= 16) score += 10
    const has = (pred: (c: string) => boolean): boolean => [...p].some(pred)
    if (has((c) => c >= 'a' && c <= 'z')) score += 10
    if (has((c) => c >= 'A' && c <= 'Z')) score += 10
    if (has((c) => c >= '0' && c <= '9')) score += 10
    if (has((c) => !/[a-zA-Z0-9]/.test(c))) score += 15
    const hits = COMMON_PWDS.filter((w) => p.toLowerCase().includes(w))
    if (hits.length) score -= 20
    if (new Set(p).size === 1) score -= 15
    let seq = false
    const codes = [...p].map((c) => c.charCodeAt(0))
    for (let i = 0; i + 2 < codes.length; i++) {
      if (
        (codes[i + 1]! - codes[i]! === 1 && codes[i + 2]! - codes[i + 1]! === 1) ||
        (codes[i]! - codes[i + 1]! === 1 && codes[i + 1]! - codes[i + 2]! === 1)
      )
        seq = true
    }
    if (seq) score -= 10
    score = Math.max(0, Math.min(100, score))
    return {
      primary: { value: String(score), unit: '/ 100' },
      rows: [
        { label: '强度', value: score < 40 ? '弱' : score < 70 ? '中' : '强' },
        { label: '常见弱口令', value: hits.length ? hits.join(', ') : '未命中' },
        { label: '顺序序列', value: seq ? '命中（如 abc/321）' : '未命中' }
      ]
    }
  },
  pyCode: (v) => {
    const p = str(v.value)
    if (!p) return INVALID_CODE
    return `"""密码强度评分（口径与页面一致：黄金用例钉死）。"""
COMMON = ${JSON.stringify(COMMON_PWDS)}
p = ${JSON.stringify(p)}
score = 0
for th in (6, 8, 12, 16):
    if len(p) >= th:
        score += 10
if any(c.islower() for c in p): score += 10
if any(c.isupper() for c in p): score += 10
if any(c.isdigit() for c in p): score += 10
if any(not c.isalnum() for c in p): score += 15
hits = [w for w in COMMON if w in p.lower()]
if hits: score -= 20
if len(set(p)) == 1: score -= 15
codes = [ord(c) for c in p]
seq = any(b - a == 1 and c2 - b == 1 or a - b == 1 and b - c2 == 1
          for a, b, c2 in zip(codes, codes[1:], codes[2:]))
if seq: score -= 10
score = max(0, min(100, score))
print(score, "弱" if score < 40 else "中" if score < 70 else "强")
`
  }
}

export const DEVTOOL_SCHEMAS: InteractiveToolSchema[] = [
  regexTesterSchema,
  jsonFormatSchema,
  jsonToDataclassSchema,
  csvJsonSchema,
  timestampSchema,
  uuidSchema,
  colorSchema,
  unitConvertSchema,
  pwdStrengthSchema
]
