// tool-schemas-w13.ts：W13 增补批 ×10——把最后一批「有页化价值但未页化」的工具收进来。
// sidecar 依赖：PyYAML（yaml↔json）、difflib（标准库）、qrcode（PNG 产物走 runImages 预览）。
// 只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const MARK = 'print("<<<JSON>>>")'

// ---------------------------------------------------------------------------
// 1. YAML ↔ JSON 互转（PyYAML safe_load；方向选择）
// ---------------------------------------------------------------------------
export const yamlJsonSchema: InteractiveToolSchema = {
  id: 'interactive:yaml-json',
  title: 'YAML ↔ JSON 互转',
  description: '双向转换（PyYAML safe_load 安全口径；JSON→YAML 用 allow_unicode 保中文）。',
  tags: ['转换'],
  fields: [
    {
      key: 'direction',
      label: '方向',
      type: 'select',
      default: 'yaml2json',
      width: 'half',
      options: [
        { value: 'yaml2json', label: 'YAML → JSON' },
        { value: 'json2yaml', label: 'JSON → YAML' }
      ]
    },
    { key: 'input', label: '输入', type: 'textarea', required: true, placeholder: 'a: 1\nb: 文本 或 {"a": 1}' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.input).trim()
      ? {
          rows: [
            { label: '方向', value: str(v.direction ?? 'yaml2json') === 'yaml2json' ? 'YAML → JSON' : 'JSON → YAML' }
          ]
        }
      : { error: '请输入内容' },
  pyCode: (v) => {
    const input = str(v.input)
    if (!input.trim()) return '# 输入内容后自动生成代码'
    if (str(v.direction ?? 'yaml2json') === 'yaml2json') {
      return `"""YAML → JSON（safe_load）。"""
import json

import yaml

data = yaml.safe_load(${JSON.stringify(input)})
print("<<<JSON>>>")
print(json.dumps({"text": json.dumps(data, ensure_ascii=False, indent=2)}, ensure_ascii=False))
print("<<<END>>>")
`
    }
    return `"""JSON → YAML（allow_unicode 保中文）。"""
import json

import yaml

data = json.loads(${JSON.stringify(input)})
print("<<<JSON>>>")
print(json.dumps({"text": yaml.dump(data, allow_unicode=True, sort_keys=False)}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 2. Base64 编解码（纯前端；UTF-8 安全）
// ---------------------------------------------------------------------------
export const base64Schema: InteractiveToolSchema = {
  id: 'interactive:base64',
  title: 'Base64 编解码',
  description: '文本 ↔ Base64（UTF-8 安全：中文先编码字节再转，不会乱码）。',
  tags: ['编码'],
  fields: [
    {
      key: 'mode',
      label: '方向',
      type: 'select',
      default: 'encode',
      width: 'half',
      options: [
        { value: 'encode', label: '编码（文本 → Base64）' },
        { value: 'decode', label: '解码（Base64 → 文本）' }
      ]
    },
    { key: 'input', label: '输入', type: 'textarea', required: true, placeholder: 'Hello 或 SGVsbG8=' }
  ],
  compute: (v) => {
    const input = str(v.input)
    if (!input) return { error: '请输入内容' }
    try {
      if (str(v.mode ?? 'encode') === 'encode') {
        const bytes = new TextEncoder().encode(input)
        const b64 = btoa(String.fromCharCode(...bytes))
        return { primary: { value: b64.slice(0, 24) + (b64.length > 24 ? '…' : '') }, text: b64 }
      }
      const bin = atob(input.replace(/\s+/g, ''))
      const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0))
      return { text: new TextDecoder().decode(bytes) }
    } catch (e) {
      return { error: `转换失败：${(e as Error).message}` }
    }
  },
  pyCode: (v) => {
    const input = str(v.input)
    if (!input) return '# 输入内容后自动生成代码'
    if (str(v.mode ?? 'encode') === 'encode') {
      return `"""Base64 编码（UTF-8 字节口径）。"""
import base64

print(base64.b64encode(${JSON.stringify(input)}.encode("utf-8")).decode())
`
    }
    return `"""Base64 解码。"""
import base64

print(base64.b64decode(${JSON.stringify(input)}).decode("utf-8"))
`
  }
}

// ---------------------------------------------------------------------------
// 3. URL 编解码（纯前端）
// ---------------------------------------------------------------------------
export const urlCodecSchema: InteractiveToolSchema = {
  id: 'interactive:url-codec',
  title: 'URL 编解码',
  description: 'encodeURIComponent / decodeURIComponent 口径（保留 URL 结构请先拆分参数）。',
  tags: ['编码'],
  fields: [
    {
      key: 'mode',
      label: '方向',
      type: 'select',
      default: 'encode',
      width: 'half',
      options: [
        { value: 'encode', label: '编码' },
        { value: 'decode', label: '解码' }
      ]
    },
    { key: 'input', label: '输入', type: 'textarea', required: true, placeholder: '中文参数 或 %E4%B8%AD%E6%96%87' }
  ],
  compute: (v) => {
    const input = str(v.input)
    if (!input) return { error: '请输入内容' }
    try {
      return {
        text: str(v.mode ?? 'encode') === 'encode' ? encodeURIComponent(input) : decodeURIComponent(input)
      }
    } catch (e) {
      return { error: `转换失败：${(e as Error).message}` }
    }
  },
  pyCode: (v) => {
    const input = str(v.input)
    if (!input) return '# 输入内容后自动生成代码'
    if (str(v.mode ?? 'encode') === 'encode') {
      return `"""URL 编码（quote 对齐 encodeURIComponent 的严格口径）。"""
from urllib.parse import quote

print(quote(${JSON.stringify(input)}, safe=""))
`
    }
    return `"""URL 解码。"""
from urllib.parse import unquote

print(unquote(${JSON.stringify(input)}))
`
  }
}

// ---------------------------------------------------------------------------
// 4. 文本对比（difflib unified diff）
// ---------------------------------------------------------------------------
export const textDiffSchema: InteractiveToolSchema = {
  id: 'interactive:text-diff',
  title: '文本对比',
  description: 'difflib unified diff：两段文本逐行对比，增删行 +/- 标注。',
  tags: ['文本'],
  fields: [
    { key: 'before', label: '原文', type: 'textarea', required: true, placeholder: '原始文本…' },
    { key: 'after', label: '新文', type: 'textarea', required: true, placeholder: '修改后文本…' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.before).trim() && !str(v.after).trim()) return { error: '请输入两段文本' }
    return { rows: [{ label: '状态', value: '点击「运行」对比' }] }
  },
  pyCode: (v) => {
    const before = str(v.before)
    const after = str(v.after)
    if (!before.trim() && !after.trim()) return '# 输入两段文本后自动生成代码'
    return `"""文本对比（difflib unified）。"""
import difflib
import json

diff = list(difflib.unified_diff(
    ${JSON.stringify(before)}.splitlines(),
    ${JSON.stringify(after)}.splitlines(),
    fromfile="原文", tofile="新文", lineterm="",
))
print("<<<JSON>>>")
print(json.dumps({"text": "\\n".join(diff) or "（两段文本完全一致）"}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 5. 二维码生成器（qrcode → PNG → runImages 抽屉预览）
// ---------------------------------------------------------------------------
export const qrcodeGenSchema: InteractiveToolSchema = {
  id: 'interactive:qrcode-gen',
  title: '二维码生成器',
  description: '文本/链接 → PNG 二维码（产物是图片，抽屉直接预览下载）。',
  tags: ['生成器'],
  fields: [{ key: 'text', label: '内容', type: 'textarea', required: true, placeholder: '文本或链接 https://…' }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.text).trim()
      ? { rows: [{ label: '内容', value: str(v.text).slice(0, 60), copy: true }] }
      : { error: '请输入内容' },
  pyCode: (v) => {
    const text = str(v.text)
    if (!text.trim()) return '# 输入内容后自动生成代码'
    return `"""二维码生成。"""
import json

import qrcode

img = qrcode.make(${JSON.stringify(text)})
img.save("qrcode.png")
print(f"已生成 qrcode.png（{img.size[0]}×{img.size[1]}）")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "qrcode.png", "copy": True},
                           {"label": "尺寸", "value": f"{img.size[0]}×{img.size[1]}"}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 6. 编码修复器（文件 → 探测 → 转 UTF-8；try-list 口径与原工具一致）
// ---------------------------------------------------------------------------
export const encodingFixSchema: InteractiveToolSchema = {
  id: 'interactive:encoding-fix',
  title: '编码修复器',
  description: '检测文本文件编码（utf-8/gbk/latin-1 试探）并转为 UTF-8（产物在工作区，检测报告即时呈现）。',
  tags: ['文本', '文件'],
  fields: [{ key: 'file', label: '文本文件', type: 'file', required: true, accept: ['txt', 'csv', 'md', 'log'] }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '文件', value: str(v.file), copy: true }] } : { error: '请选择文件' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择文件后自动生成代码'
    return `"""编码修复：GBK/Latin1 → UTF-8（试探口径与原工具一致）。"""
import json

data = open(${JSON.stringify(file)}, "rb").read()
detected = None
for enc in ("utf-8", "gbk", "latin-1"):
    try:
        text = data.decode(enc)
        detected = enc
        break
    except (UnicodeDecodeError, UnicodeError):
        continue
if detected is None:
    raise SystemExit("无法识别编码")
open("fixed.utf8.txt", "w", encoding="utf-8").write(text)
print(f"检测到编码: {detected}，共 {len(text)} 字符，已转出 fixed.utf8.txt")
print("<<<JSON>>>")
print(json.dumps({"rows": [
    {"label": "检测编码", "value": detected},
    {"label": "字符数", "value": str(len(text))},
    {"label": "产物", "value": "fixed.utf8.txt"}
]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 7. 透视汇总（向导：数据 + 行/列维度 + 数值列 → 透视表格）
// ---------------------------------------------------------------------------
export const pivotSchema: InteractiveToolSchema = {
  id: 'interactive:pivot',
  title: 'Excel 透视汇总',
  description: '粘贴 CSV 数据 + 三个维度字段 → 双维聚合透视表（数值求和）。',
  tags: ['Excel', '向导'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首行表头）',
      type: 'textarea',
      required: true,
      placeholder: '部门,月份,金额\n研发,1月,120'
    },
    { key: 'rowDim', label: '行维度列', type: 'text', required: true, placeholder: '部门', width: 'half' },
    { key: 'colDim', label: '列维度列', type: 'text', required: true, placeholder: '月份', width: 'half' },
    { key: 'valCol', label: '数值列', type: 'text', required: true, placeholder: '金额', width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '粘贴数据', keys: ['data'] },
    { title: '维度与执行', keys: ['rowDim', 'colDim', 'valCol'] }
  ],
  compute: (v) =>
    str(v.data) && str(v.rowDim) && str(v.colDim) && str(v.valCol)
      ? { rows: [{ label: '数据', value: `${str(v.data).split('\n').length - 1} 行` }] }
      : { error: '请按步骤补全数据与三个维度字段' },
  pyCode: (v) => {
    const data = str(v.data)
    const rd = str(v.rowDim)
    const cd = str(v.colDim)
    const vc = str(v.valCol)
    if (!data.trim() || !rd || !cd || !vc) return '# 按步骤补全后自动生成代码'
    return `"""透视：行=${rd} 列=${cd} 值=${vc}（求和）。"""
import csv
import io
import json
from collections import defaultdict

rows = list(csv.DictReader(io.StringIO(${JSON.stringify(data)})))
pivot: dict = defaultdict(float)
colKeys: list = []
for r in rows:
    ck = r[${JSON.stringify(cd)}]
    if ck not in colKeys:
        colKeys.append(ck)
    pivot[(r[${JSON.stringify(rd)}], ck)] += float(r[${JSON.stringify(vc)}] or 0)
colKeys.sort()
rowKeys = sorted({k[0] for k in pivot})
table_rows = [[rk] + [f"{pivot.get((rk, ck), 0):g}" for ck in colKeys] for rk in rowKeys]
print("<<<JSON>>>")
print(json.dumps({"table": {"columns": [${JSON.stringify(rd)}] + colKeys, "rows": table_rows}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 8. 跨表关联（主表 + 字典表 + 各自键列 → 拼接）
// ---------------------------------------------------------------------------
export const crossJoinSchema: InteractiveToolSchema = {
  id: 'interactive:cross-join',
  title: '跨表关联',
  description: '主表 + 字典表按各自键列左连接（字典列追加到主表右侧，未命中 <未知>）。',
  tags: ['Excel', '向导'],
  fields: [
    { key: 'mainFile', label: '主表', type: 'file', required: true, accept: ['xlsx', 'csv'] },
    { key: 'lookupFile', label: '字典表', type: 'file', required: true, accept: ['xlsx', 'csv'] },
    { key: 'mainKey', label: '主表键列', type: 'text', required: true, placeholder: '工号', width: 'half' },
    { key: 'lookupKey', label: '字典表键列', type: 'text', required: true, placeholder: '工号', width: 'half' },
    { key: 'lookupVal', label: '字典表取值列', type: 'text', required: true, placeholder: '姓名', width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择两表', keys: ['mainFile', 'lookupFile'] },
    { title: '键列与执行', keys: ['mainKey', 'lookupKey', 'lookupVal'] }
  ],
  compute: (v) =>
    str(v.mainFile) && str(v.lookupFile) && str(v.mainKey) && str(v.lookupKey) && str(v.lookupVal)
      ? {
          rows: [
            { label: '主表', value: str(v.mainFile), copy: true },
            { label: '字典表', value: str(v.lookupFile), copy: true }
          ]
        }
      : { error: '请按步骤补全两表与键列' },
  pyCode: (v) => {
    const m = str(v.mainFile)
    const l = str(v.lookupFile)
    const mk = str(v.mainKey)
    const lk = str(v.lookupKey)
    const lv = str(v.lookupVal)
    if (!m || !l || !mk || !lk || !lv) return '# 按步骤补全后自动生成代码'
    return `"""跨表关联：主表 + 字典表（${lk}→${lv}）左连接。"""
import csv
import io
import json

from openpyxl import load_workbook

def xlsx_rows(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    return rows

def any_rows(path):
    return xlsx_rows(path) if path.endswith((".xlsx", ".xlsm")) else list(csv.reader(io.StringIO(open(path, encoding="utf-8-sig").read())))

main_rows = any_rows(${JSON.stringify(m)})
lookup_rows = any_rows(${JSON.stringify(l)})
m_head, m_body = main_rows[0], main_rows[1:]
l_head, l_body = lookup_rows[0], lookup_rows[1:]
mi, li, vi = m_head.index(${JSON.stringify(mk)}), l_head.index(${JSON.stringify(lk)}), l_head.index(${JSON.stringify(lv)})
lookup = {r[li]: r[vi] for r in l_body}
out_head = m_head + [${JSON.stringify(lv)}]
out_rows = [r + [lookup.get(r[mi], "<未知>")] for r in m_body]
print("<<<JSON>>>")
print(json.dumps({
    "primary": {"value": str(len(out_rows)), "unit": "行已关联"},
    "table": {"columns": out_head, "rows": [[str(c) for c in r] for r in out_rows[:30]]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 9. 数据校验（数值列范围规则 → 错误行报告）
// ---------------------------------------------------------------------------
export const dataValidateSchema: InteractiveToolSchema = {
  id: 'interactive:data-validate',
  title: 'Excel 数据校验',
  description: '对数值列做范围规则校验（min/max + 空值处理），错误行报告（原工具口径：工时 0<h≤16 的推广）。',
  tags: ['Excel', '校验'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首行表头）',
      type: 'textarea',
      required: true,
      placeholder: '日期,工时\n2026-09-21,12'
    },
    { key: 'col', label: '校验列', type: 'text', required: true, placeholder: '工时', width: 'half' },
    { key: 'min', label: '最小值（含）', type: 'number', default: 0, width: 'half' },
    { key: 'max', label: '最大值（含）', type: 'number', default: 16, width: 'half' },
    { key: 'allowEmpty', label: '允许空值', type: 'checkbox', default: true, width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '粘贴数据', keys: ['data'] },
    { title: '规则与执行', keys: ['col', 'min', 'max', 'allowEmpty'] }
  ],
  compute: (v) =>
    str(v.data) && str(v.col)
      ? {
          rows: [
            { label: '数据', value: `${str(v.data).split('\n').length - 1} 行` },
            { label: '规则', value: `${str(v.col)} ∈ [${str(v.min ?? 0)}, ${str(v.max ?? 16)}]` }
          ]
        }
      : { error: '请按步骤补全数据与规则' },
  pyCode: (v) => {
    const data = str(v.data)
    const col = str(v.col)
    const min = Number(v.min ?? 0)
    const max = Number(v.max ?? 16)
    const allow = v.allowEmpty === true
    if (!data.trim() || !col || !Number.isFinite(min) || !Number.isFinite(max)) return '# 按步骤补全后自动生成代码'
    return `"""数据校验：${col} ∈ [${min}, ${max}]${allow ? '（空值放行）' : ''}。"""
import csv
import io
import json

rows = list(csv.DictReader(io.StringIO(${JSON.stringify(data)})))
errors = []
for i, r in enumerate(rows, start=2):
    raw = (r.get(${JSON.stringify(col)}) or "").strip()
    if raw == "":
        if not (${allow ? 'True' : 'False'}):
            errors.append([str(i), "空值"])
        continue
    try:
        h = float(raw)
    except ValueError:
        errors.append([str(i), f"非数值: {raw}"])
        continue
    if not (${min} <= h <= ${max}):
        errors.append([str(i), f"超范围: {h}"])
print("<<<JSON>>>")
print(json.dumps({
    "primary": {"value": str(len(rows) - len(errors)), "unit": f"/ {len(rows)} 行通过"},
    "table": {"columns": ["行", "问题"], "rows": errors[:100]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 10. 库存盘点（纯前端：期初/入库/出库三份 CSV → 期末库存 + 补货标记）
// ---------------------------------------------------------------------------
const STOCK_THRESHOLD = 5

export const stockInventorySchema: InteractiveToolSchema = {
  id: 'interactive:stock-inventory',
  title: '库存盘点',
  description: '期初/入库/出库 三份「品名,数量」CSV → 期末库存核算 + 低库存（<5）补货标记。',
  tags: ['统计'],
  fields: [
    { key: 'opening', label: '期初库存', type: 'textarea', required: true, placeholder: '键盘,12\n鼠标,30' },
    { key: 'inflow', label: '入库', type: 'textarea', required: false, placeholder: '键盘,10' },
    { key: 'outflow', label: '出库', type: 'textarea', required: false, placeholder: '鼠标,15' }
  ],
  compute: (v) => {
    const parse = (t: string): Array<[string, number]> =>
      str(t)
        .split('\n')
        .map((ln) => ln.trim())
        .filter(Boolean)
        .map((ln) => {
          const [k, n] = ln.split(/[,，\t]/)
          return [str(k).trim(), Number(n)] as [string, number]
        })
        .filter(([k, n]) => k && Number.isFinite(n))
    const stock = new Map<string, number>()
    for (const [k, n] of parse(str(v.opening))) stock.set(k, (stock.get(k) ?? 0) + n)
    if (!stock.size) return { error: '请至少填写期初库存' }
    for (const [k, n] of parse(str(v.inflow))) stock.set(k, (stock.get(k) ?? 0) + n)
    for (const [k, n] of parse(str(v.outflow))) stock.set(k, (stock.get(k) ?? 0) - n)
    const rows = [...stock.entries()]
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([k, n]) => [k, String(n), n < STOCK_THRESHOLD ? '⚠️ 需补货' : ''])
    return {
      rows: [
        { label: '品类', value: String(stock.size) },
        { label: '需补货', value: String(rows.filter((r) => r[2]).length) }
      ],
      table: { columns: ['品名', '期末库存', '标记'], rows }
    }
  },
  pyCode: (v) => {
    const parse = (t: string): string => JSON.stringify(t)
    if (!str(v.opening).trim()) return '# 填写期初库存后自动生成代码'
    return `"""库存盘点：期初/入库/出库 核算。"""
from collections import defaultdict

def parse(t):
    d = {}
    for ln in t.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        k, _, n = ln.partition(",")
        d[k.strip()] = d.get(k.strip(), 0) + int(n)
    return d

stock = defaultdict(int, parse(${parse(str(v.opening))}))
for k, n in parse(${parse(str(v.inflow ?? ''))}).items():
    stock[k] += n
for k, n in parse(${parse(str(v.outflow ?? ''))}).items():
    stock[k] -= n
print("<<<JSON>>>")
print(json.dumps({
    "table": {"columns": ["品名", "期末库存", "标记"],
              "rows": [[k, str(n), "⚠️ 需补货" if n < 5 else ""] for k, n in sorted(stock.items())]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const W13_SCHEMAS: InteractiveToolSchema[] = [
  yamlJsonSchema,
  base64Schema,
  urlCodecSchema,
  textDiffSchema,
  qrcodeGenSchema,
  encodingFixSchema,
  pivotSchema,
  crossJoinSchema,
  dataValidateSchema,
  stockInventorySchema
]
