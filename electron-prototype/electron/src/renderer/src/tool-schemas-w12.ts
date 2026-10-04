// tool-schemas-w12.ts：W12 收官批——Office 演示教学改造（硬编码演示 → 操作用户内容/文件）
// + 字符方阵/文本表格（纯前端）+ 站点监控/文件变更对比（sidecar）。
// 产物形态：openpyxl / python-docx / python-pptx 写 xlsx/docx/pptx 到运行工作区，
// 结果 JSON 报告产物名与规模（二进制产物暂不支持抽屉下载，见规划 §3.3 注）。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const MARK = 'print("<<<JSON>>>")'

// CSV 行解析（数据 textarea 的统一入口；支持引号转义的最小实现）
const CSV_PARSE_PY = `import csv as _csv
import io as _io
import json

def parse_rows(text):
    return [r for r in _csv.reader(_io.StringIO(text.strip())) if r]
`

// ---------------------------------------------------------------------------
// 纯前端 1：字符方阵（吸收 bulk_basics ×4 变体）
// ---------------------------------------------------------------------------
export const charMatrixSchema: InteractiveToolSchema = {
  id: 'interactive:char-matrix',
  title: '字符方阵',
  description: '按规则生成 size×size 字符图案（pattern=(r*c+r+c) mod len，可视纹理）。',
  tags: ['图案'],
  fields: [
    { key: 'size', label: '边长', type: 'number', default: 9, width: 'half', help: '5~40' },
    { key: 'chars', label: '字符集', type: 'text', default: '◆◇', width: 'half' }
  ],
  compute: (v) => {
    const size = Math.trunc(Number(v.size ?? 9))
    if (!Number.isFinite(size) || size < 5 || size > 40) return { error: '边长需为 5~40 的整数' }
    const chars = str(v.chars ?? '◆◇')
    if (!chars) return { error: '字符集不能为空' }
    const rows: string[] = []
    for (let r = 0; r < size; r++) {
      let row = ''
      for (let c = 0; c < size; c++) row += chars[(r * c + r + c) % chars.length]
      rows.push(row)
    }
    return { primary: { value: `${size}×${size}` }, text: rows.join('\n') }
  },
  pyCode: (v) => {
    const size = Math.trunc(Number(v.size ?? 9))
    const chars = str(v.chars ?? '◆◇')
    if (!Number.isFinite(size) || size < 5 || !chars) return '# 补全参数后自动生成代码'
    return `"""字符方阵：${size}×${size}，字符集 '${chars}'。"""
size, chars = ${size}, "${chars}"
for r in range(size):
    row = "".join(chars[(r * c + r + c) % len(chars)] for c in range(size))
    print(row)
`
  }
}

// ---------------------------------------------------------------------------
// 纯前端 2：文本表格（吸收 bulk_basics ×3 变体）
// ---------------------------------------------------------------------------
export const textTableSchema: InteractiveToolSchema = {
  id: 'interactive:text-table',
  title: '文本表格',
  description: '粘贴 CSV 数据 → 生成对齐的 Markdown 表格（列宽自适应，纯前端）。',
  tags: ['文本'],
  fields: [
    { key: 'data', label: '数据（CSV，首行表头）', type: 'textarea', required: true, placeholder: '名称,数量\n苹果,12' }
  ],
  compute: (v) => {
    const text = str(v.data).trim()
    if (!text) return { error: '请粘贴数据' }
    const rows = text.split('\n').map((ln) => ln.split(',').map((c) => c.trim()))
    const width = rows[0]!.map((_, i) => Math.max(...rows.map((r) => (r[i] ?? '').length)))
    const lines = [
      `| ${rows[0]!.map((c, i) => (c ?? '').padEnd(width[i]!)).join(' | ')} |`,
      `|${width.map((w) => '-'.repeat(w + 2)).join('|')}|`,
      ...rows.slice(1).map((r) => `| ${width.map((w, i) => (r[i] ?? '').padEnd(w)).join(' | ')} |`)
    ]
    return { primary: { value: String(rows.length - 1), unit: '行数据' }, text: lines.join('\n') }
  },
  pyCode: (v) => {
    const text = str(v.data).trim()
    if (!text) return '# 粘贴数据后自动生成代码'
    return `"""文本表格：宽度自适应对齐输出。"""
data = [
${text
  .split('\n')
  .map(
    (ln) =>
      '    [' +
      ln
        .split(',')
        .map((c) => JSON.stringify(c.trim()))
        .join(', ') +
      '],'
  )
  .join('\n')}
]
widths = [max(len(str(row[i])) for row in data) for i in range(len(data[0]))]
print("| " + " | ".join(h.ljust(w) for h, w in zip(data[0], widths)) + " |")
print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
for r in data[1:]:
    print("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |")
`
  }
}

// ---------------------------------------------------------------------------
// 站点可用性监控（URLs → 状态码表格）
// ---------------------------------------------------------------------------
export const siteMonitorSchema: InteractiveToolSchema = {
  id: 'interactive:site-monitor',
  title: '站点可用性监控',
  description: '批量探测 URL 列表：状态码/耗时（每行一个 URL，手动触发；监控告警请用系统级工具）。',
  tags: ['网络', '监控'],
  fields: [
    {
      key: 'urls',
      label: 'URL 列表（每行一个）',
      type: 'textarea',
      required: true,
      placeholder: 'https://example.com\nhttps://api.example.com/health'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    const urls = str(v.urls)
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
    if (!urls.length) return { error: '请输入至少一个 URL' }
    return { rows: [{ label: '站点数', value: String(urls.length) }] }
  },
  pyCode: (v) => {
    const urls = str(v.urls)
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
    if (!urls.length) return '# 输入 URL 列表后自动生成代码'
    return `"""站点可用性批量探测。"""
import json
import time

import requests

urls = ${JSON.stringify(urls)}
rows = []
for u in urls:
    t0 = time.monotonic()
    try:
        resp = requests.get(u, timeout=10)
        rows.append([u, str(resp.status_code), f"{(time.monotonic() - t0) * 1000:.0f} ms"])
    except Exception as e:
        rows.append([u, "ERR", str(e)[:40]])
ok = sum(1 for r in rows if r[1].startswith("2"))
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": f"{ok}/{len(rows)}", "unit": "可用"},
                  "table": {"columns": ["URL", "状态", "耗时"], "rows": rows}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 文件变更对比（两次快照 diff：运行时长由「间隔秒数」参数决定）
// ---------------------------------------------------------------------------
export const fileWatchSchema: InteractiveToolSchema = {
  id: 'interactive:file-watch',
  title: '文件变更对比',
  description: '对目录做两次快照（间隔可调），报告新增/删除/修改的文件（按 mtime+大小判定）。',
  tags: ['文件', '监控'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    {
      key: 'interval',
      label: '快照间隔(秒)',
      type: 'number',
      default: 10,
      width: 'half',
      help: '运行期间会等待这段时间'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.dir)) return { error: '请选择目录' }
    const sec = Math.trunc(Number(v.interval ?? 10))
    if (!Number.isFinite(sec) || sec < 2 || sec > 120) return { error: '间隔需为 2~120 秒' }
    return {
      rows: [
        { label: '目录', value: str(v.dir), copy: true },
        { label: '间隔', value: `${sec} 秒` }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const sec = Math.trunc(Number(v.interval ?? 10))
    if (!dir || !Number.isFinite(sec) || sec < 2) return '# 选择目录后自动生成代码'
    return `"""文件变更对比：两次快照（间隔 ${sec}s，按 mtime+大小判定）。"""
import json
import time
from pathlib import Path

def snapshot():
    return {str(f): (f.stat().st_mtime, f.stat().st_size) for f in Path(${JSON.stringify(dir)}).rglob("*") if f.is_file()}

print("第一次快照…")
before = snapshot()
print(f"等待 ${sec} 秒后做第二次快照…")
time.sleep(${sec})
after = snapshot()
added = sorted(set(after) - set(before))
removed = sorted(set(before) - set(after))
changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
rows = [["新增", p] for p in added] + [["删除", p] for p in removed] + [["修改", p] for p in changed]
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(rows)), "unit": "处变更"},
                  "table": {"columns": ["变更", "路径"], "rows": rows[:200]}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// Excel 改造 ×10（数据/文件输入 → openpyxl 产物 xlsx）
// ---------------------------------------------------------------------------
const XLSX_OUT = (name: string): string => `wb.save(${JSON.stringify(name)})
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": ${JSON.stringify(name)}},
                           {"label": "规模", "value": f"{ws.max_row} 行 × {ws.max_column} 列"}]}, ensure_ascii=False))
print("<<<END>>>")
`

const XLSX_PRELUDE = (dataVar: string) => `${CSV_PARSE_PY}
def _coerce(c):
    if c == "": return None
    if c == "true": return True
    if c == "false": return False
    try:
        return int(c)
    except ValueError:
        pass
    try:
        return float(c)
    except ValueError:
        pass
    return c

rows = parse_rows(${dataVar})
if len(rows) < 1:
    raise SystemExit("请提供至少一行表头")
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
for r in rows:
    ws.append([_coerce(c) for c in r])
`

function excelTool(
  partial: Omit<InteractiveToolSchema, 'id' | 'title' | 'description' | 'fields' | 'pyCode'> & {
    id: string
    title: string
    description: string
    fields: FieldSpec[]
    tags?: string[]
    body: (dataVar: string, v: Record<string, unknown>) => string
  }
): InteractiveToolSchema {
  return {
    ...partial,
    tags: partial.tags ?? ['Excel'],
    computeVia: 'sidecar',
    compute: (v) => {
      for (const f of partial.fields) {
        if (f.required && !str(v[f.key])) return { error: `请补全「${f.label}」` }
      }
      return {
        rows: partial.fields
          .filter((f) => f.key !== 'data')
          .map((f) => ({ label: f.label, value: str(v[f.key]) || '—' }))
      }
    },
    pyCode: (v) => {
      for (const f of partial.fields) {
        if (f.required && !str(v[f.key])) return '# 补全必填项后自动生成代码'
      }
      return XLSX_PRELUDE(str(v.data) || '""') + partial.body('rows', v) + '\n' + XLSX_OUT('output.xlsx')
    }
  }
}

const DATA_FIELD = {
  key: 'data',
  label: '表数据（CSV，首行表头）',
  type: 'textarea' as const,
  required: true,
  placeholder: '名称,数量\n苹果,12'
}

export const excelBuildSchema: InteractiveToolSchema = excelTool({
  id: 'interactive:excel-build',
  title: 'Excel 建表',
  description: '粘贴 CSV 数据 → 生成 xlsx 工作簿（自动识别数字/布尔/空值）。',
  tags: ['Excel'],
  fields: [DATA_FIELD],
  body: () => ''
})

export const excelStyleSchema: InteractiveToolSchema = excelTool({
  id: 'interactive:excel-style',
  title: 'Excel 样式',
  description: '生成带表头样式（加粗/填充/边框）的工作簿。',
  tags: ['Excel'],
  fields: [DATA_FIELD],
  body: () => `from openpyxl.styles import Font, PatternFill, Border, Side

thin = Side(style="thin")
for cell in ws[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="2F5496")
    cell.border = Border(thin, thin, thin, thin)
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.border = Border(thin, thin, thin, thin)
ws.column_dimensions["A"].width = 22
`
})

export const excelFormulaSchema: InteractiveToolSchema = {
  ...excelStyleSchema,
  id: 'interactive:excel-formula',
  title: 'Excel 公式与汇总',
  description: '数据末列追加 SUM 汇总公式行（Excel 打开时计算）。',
  pyCode: (v) =>
    XLSX_PRELUDE(str(v.data) || '""') +
    `import openpyxl.utils

last_col = ws.max_column
sum_col = last_col + 1
ws.cell(row=1, column=sum_col, value="合计")
for r in range(2, ws.max_row + 1):
    ws.cell(row=r, column=sum_col, value=f"=SUM(A{{r}}:{{openpyxl.utils.get_column_letter(last_col)}}{{r}})")
` +
    XLSX_OUT('output.xlsx')
}

export const excelChartSchema: InteractiveToolSchema = {
  id: 'interactive:excel-chart',
  title: 'Excel 内嵌图表',
  description: '生成数据表 + 内嵌柱状图（首列为类别，第二列为数值）。',
  tags: ['Excel'],
  fields: [DATA_FIELD],
  pyCode: (v) => {
    const data = str(v.data)
    if (!data.trim()) return '# 粘贴数据后自动生成代码'
    return (
      `${XLSX_PRELUDE(JSON.stringify(data))}
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.title = "数据图表"
data_ref = Reference(ws, min_col=2, min_row=1, max_row=ws.max_row)
cats = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "F2")
` +
      XLSX_OUT('output.xlsx') +
      '\n'
    )
  }
}

export const excelFreezeSchema: InteractiveToolSchema = excelTool({
  id: 'interactive:excel-freeze',
  title: 'Excel 冻结表头',
  description: '生成冻结首行的工作簿（滚动时表头常驻）。',
  tags: ['Excel'],
  fields: [DATA_FIELD],
  body: () => 'ws.freeze_panes = "A2"\n'
})

export const excelCondFmtSchema: InteractiveToolSchema = {
  ...excelStyleSchema,
  id: 'interactive:excel-condfmt',
  title: 'Excel 条件格式',
  description: '对第二列数值加色阶条件格式（数据条）。',
  pyCode: (v) =>
    XLSX_PRELUDE(str(v.data) || '""') +
    `from openpyxl.formatting.rule import DataBarRule

rule = DataBarRule(start_type="min", end_type="max", color="638EC6")
ws.conditional_formatting.add(f"B2:B{ws.max_row}", rule)
` +
    XLSX_OUT('output.xlsx') +
    '\n'
}

export const excelSortSchema: InteractiveToolSchema = {
  ...excelStyleSchema,
  id: 'interactive:excel-sort',
  title: 'Excel 数据排序',
  description: '按第一列排序后写入工作簿（数字/字符串自然序）。',
  pyCode: (v) =>
    XLSX_PRELUDE(str(v.data) || '""') +
    `body = rows[1:]
body.sort(key=lambda r: (isinstance(r[0], str), r[0]))
for r in body:
    ws.append(r)
` +
    XLSX_OUT('output.xlsx') +
    '\n'
}

export const excelProtectSchema: InteractiveToolSchema = excelTool({
  id: 'interactive:excel-protect',
  title: 'Excel 工作表保护',
  description: '生成开启工作表保护（可设密码）的工作簿：仅读不改。',
  tags: ['Excel'],
  fields: [
    DATA_FIELD,
    { key: 'password', label: '保护密码', type: 'text', default: '', width: 'half', help: '留空 = 无密码保护' }
  ],
  body: (_d, v) => `ws.protection.password = ${JSON.stringify(str(v.password ?? ''))}\nws.protection.sheet = True\n`
})

export const excelCommentSchema: InteractiveToolSchema = {
  ...excelStyleSchema,
  id: 'interactive:excel-comment',
  title: 'Excel 单元格批注',
  description: '给表头每个单元格加批注（内容=该列名）。',
  pyCode: (v) =>
    XLSX_PRELUDE(str(v.data) || '""') +
    `from openpyxl.comments import Comment

for cell in ws[1]:
    cell.comment = Comment(f"列：{cell.value}", "PyCase")
` +
    XLSX_OUT('output.xlsx') +
    '\n'
}

export const excelMergeHeaderSchema: InteractiveToolSchema = {
  ...excelStyleSchema,
  id: 'interactive:excel-merge-header',
  title: 'Excel 合并单元格表头',
  description: '首行跨全列合并为大标题（第二行为列头）。',
  pyCode: (v) =>
    XLSX_PRELUDE(str(v.data) || '""') +
    `import openpyxl.utils

ws.insert_rows(1)
last = openpyxl.utils.get_column_letter(ws.max_column)
ws.merge_cells(f"A1:{{last}}1")
ws.cell(row=1, column=1, value="报表标题（可改）")
` +
    XLSX_OUT('output.xlsx')
}

// ---------------------------------------------------------------------------
// Word ×3 / PPT ×1 / 文本 ×3（docx / pptx / eml / md）
// ---------------------------------------------------------------------------
const DOCX_OUT = (name: string): string => `doc.save(${JSON.stringify(name)})
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": ${JSON.stringify(name)}}]}, ensure_ascii=False))
print("<<<END>>>")
`

export const wordDocSchema: InteractiveToolSchema = {
  id: 'interactive:word-doc',
  title: 'Word 文档生成',
  description: '按 Markdown 子集生成 docx：# 标题、- 列表、普通段落（python-docx）。',
  tags: ['Word'],
  fields: [
    {
      key: 'content',
      label: '内容（# 标题 / - 列表 / 段落）',
      type: 'textarea',
      required: true,
      placeholder: '# 报告标题\n正文段落…\n- 要点一'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.content).trim() ? { rows: [{ label: '产物', value: 'document.docx' }] } : { error: '请输入内容' },
  pyCode: (v) => {
    const content = str(v.content)
    if (!content.trim()) return '# 输入内容后自动生成代码'
    return `"""Markdown 子集 → docx。"""
import json

from docx import Document

doc = Document()
for ln in ${JSON.stringify(content)}.split("\\n"):
    s = ln.strip()
    if not s:
        continue
    if s.startswith("# "):
        doc.add_heading(s[2:], level=1)
    elif s.startswith("## "):
        doc.add_heading(s[3:], level=2)
    elif s.startswith("- "):
        doc.add_paragraph(s[2:], style="List Bullet")
    else:
        doc.add_paragraph(s)
${DOCX_OUT('document.docx')}`
  }
}

export const wordTableSchema: InteractiveToolSchema = {
  id: 'interactive:word-table',
  title: 'Word 表格',
  description: 'CSV 数据 → 带表头样式的 docx 表格。',
  tags: ['Word'],
  fields: [
    {
      key: 'data',
      label: '表数据（CSV，首行表头）',
      type: 'textarea',
      required: true,
      placeholder: '名称,数量\n苹果,12'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) => (str(v.data).trim() ? { rows: [{ label: '产物', value: 'table.docx' }] } : { error: '请粘贴数据' }),
  pyCode: (v) => {
    const data = str(v.data)
    if (!data.trim()) return '# 粘贴数据后自动生成代码'
    return `"""CSV → docx 表格。"""
import json
import csv
import io

from docx import Document

rows = list(csv.reader(io.StringIO(${JSON.stringify(data)})))
doc = Document()
table = doc.add_table(rows=len(rows), cols=len(rows[0]))
table.style = "Table Grid"
for i, row in enumerate(rows):
    for j, cell in enumerate(row):
        table.cell(i, j).text = str(cell)
if rows:
    for cell in table.rows[0].cells:
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
${DOCX_OUT('table.docx')}`
  }
}

export const wordLettersSchema: InteractiveToolSchema = {
  id: 'interactive:word-letters',
  title: 'Word 批量函件',
  description: '模板（{{姓名}} 等占位）+ CSV 数据 → 每行一份 docx（产物在工作区）。',
  tags: ['Word', '批量'],
  fields: [
    {
      key: 'template',
      label: '模板（{{列名}} 占位）',
      type: 'textarea',
      required: true,
      placeholder: '尊敬的{{姓名}}：\n您的订单 {{订单号}} 已发货。'
    },
    {
      key: 'data',
      label: '数据（CSV，首行表头，含模板用到的列）',
      type: 'textarea',
      required: true,
      placeholder: '姓名,订单号\n张三,A1001'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.template) && str(v.data)
      ? { rows: [{ label: '产物', value: '每行一份 docx（工作区）' }] }
      : { error: '请补全模板与数据' },
  pyCode: (v) => {
    const tpl = str(v.template)
    const data = str(v.data)
    if (!tpl || !data.trim()) return '# 补全模板与数据后自动生成代码'
    return `"""模板 + CSV → 批量函件。"""
import csv
import io

from docx import Document

template = ${JSON.stringify(tpl)}
rows = list(csv.DictReader(io.StringIO(${JSON.stringify(data)})))
for i, rec in enumerate(rows, 1):
    text = template
    for k, val in rec.items():
        text = text.replace("{{" + k + "}}", str(val))
    doc = Document()
    for para in text.split("\\n"):
        if para.strip():
            doc.add_paragraph(para)
    doc.save(f"letter_{i:03d}.docx")
print(f"已生成 {len(rows)} 份函件")
${MARK}
import json as _json
print(_json.dumps({"primary": {"value": str(len(rows)), "unit": "份 docx"}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const pptSlidesSchema: InteractiveToolSchema = {
  id: 'interactive:ppt-slides',
  title: 'PPT 幻灯片生成',
  description: '每两行一张片（标题/正文，空行分隔多片）→ pptx（python-pptx）。',
  tags: ['PPT'],
  fields: [
    {
      key: 'slides',
      label: '幻灯片（每行「标题|正文」，空行分片）',
      type: 'textarea',
      required: true,
      placeholder: '封面|我的演示\n要点|第一点\n要点|第二点'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.slides).trim() ? { rows: [{ label: '产物', value: 'slides.pptx' }] } : { error: '请输入幻灯片内容' },
  pyCode: (v) => {
    const slides = str(v.slides)
    if (!slides.trim()) return '# 输入幻灯片内容后自动生成代码'
    return `"""文本 → pptx（每行「标题|正文」，空行分片）。"""
from pptx import Presentation

pres = Presentation()
for block in ${JSON.stringify(slides)}.split("\\n\\n"):
    lines = [l for l in block.splitlines() if l.strip()]
    if not lines:
        continue
    title, _, body = lines[0].partition("|")
    slide = pres.slides.add_slide(pres.slide_layouts[1])
    slide.shapes.title.text = title.strip()
    slide.placeholders[1].text = body.strip()
pres.save("slides.pptx")
${MARK}
import json as _json
print(_json.dumps({"rows": [{"label": "产物", "value": "slides.pptx"}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const dailyReportSchema: InteractiveToolSchema = {
  id: 'interactive:daily-report',
  title: '文本日报生成',
  description: '字段（今日完成/明日计划/问题）→ 结构化日报 Markdown 文本。',
  tags: ['文本'],
  fields: [
    { key: 'done', label: '今日完成（每行一条）', type: 'textarea', required: true },
    { key: 'plan', label: '明日计划（每行一条）', type: 'textarea', required: false },
    { key: 'issues', label: '问题与风险', type: 'textarea', required: false }
  ],
  compute: (v) => {
    const done = str(v.done).trim()
    if (!done) return { error: '请填写今日完成' }
    const li = (t: string): string =>
      t
        .split('\n')
        .filter(Boolean)
        .map((x) => `- ${x.trim()}`)
        .join('\n')
    const md = `## 今日完成\n${li(done)}\n${str(v.plan).trim() ? `\n## 明日计划\n${li(str(v.plan))}\n` : ''}${str(v.issues).trim() ? `\n## 问题与风险\n${li(str(v.issues))}\n` : ''}`
    return { text: md }
  },
  pyCode: (v) => {
    const done = str(v.done).trim()
    if (!done) return '# 填写今日完成后自动生成代码'
    return `"""日报生成。"""
def li(t):
    return "\\n".join("- " + x.strip() for x in t.splitlines() if x.strip())

md = "## 今日完成\\n" + li(${JSON.stringify(done)})
${str(v.plan).trim() ? `md += "\\n\\n## 明日计划\\n" + li(${JSON.stringify(str(v.plan))})\n` : ''}${str(v.issues).trim() ? `md += "\\n\\n## 问题与风险\\n" + li(${JSON.stringify(str(v.issues))})\n` : ''}print(md)
`
  }
}

export const mdTodoSchema: InteractiveToolSchema = {
  id: 'interactive:md-todo',
  title: 'Markdown 待办清单',
  description: '待办文本（每行一条，可带 @负责人 和 !优先级）→ 带复选框的 Markdown 清单。',
  tags: ['Markdown'],
  fields: [
    {
      key: 'items',
      label: '待办（每行一条；@负责人 !P0/P1）',
      type: 'textarea',
      required: true,
      placeholder: '写周报 @张三 !P0\n修登录页 bug'
    }
  ],
  compute: (v) => {
    const items = str(v.items)
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
    if (!items.length) return { error: '请输入待办' }
    const md = items
      .map((raw) => {
        const pri = /!(P\d)/.exec(raw)?.[1] ?? ''
        const owner = /@(\S+)/.exec(raw)?.[1] ?? ''
        const text = raw
          .replace(/!(P\d)/, '')
          .replace(/@(\S+)/, '')
          .trim()
        const meta = [owner && `@${owner}`, pri].filter(Boolean).join(' ')
        return `- [ ] ${text}${meta ? `（${meta}）` : ''}`
      })
      .join('\n')
    return { text: md }
  },
  pyCode: (v) => {
    const items = str(v.items)
    if (!items.trim()) return '# 输入待办后自动生成代码'
    return `"""待办 → Markdown 清单。"""
import re

items = ${JSON.stringify(items)}.splitlines()
for raw in items:
    if not raw.strip():
        continue
    pri = (re.search(r"!(P\\d)", raw) or [None, ""])[1]
    owner_m = re.search(r"@\\S+", raw)
    owner = owner_m.group(0) if owner_m else ""
    text = re.sub(r"!(P\\d)|@\\S+", "", raw).strip()
    meta = "（" + " ".join(x for x in (owner, pri) if x) + "）" if (owner or pri) else ""
    print(f"- [ ] {{text}}{{meta}}")
`
  }
}

export const mailDraftSchema: InteractiveToolSchema = {
  id: 'interactive:mail-draft',
  title: '邮件构造与落盘',
  description: '字段化构造邮件（收件人/主题/正文）→ 标准 .eml 文件（落盘工作区，可直接拖入邮件客户端）。',
  tags: ['邮件'],
  fields: [
    { key: 'to', label: '收件人', type: 'text', required: true, placeholder: 'someone@example.com', width: 'half' },
    { key: 'subject', label: '主题', type: 'text', required: true, width: 'half' },
    { key: 'body', label: '正文', type: 'textarea', required: true }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.to) && str(v.subject) && str(v.body)
      ? {
          rows: [
            { label: '收件人', value: str(v.to), copy: true },
            { label: '主题', value: str(v.subject) }
          ]
        }
      : { error: '请补全收件人/主题/正文' },
  pyCode: (v) => {
    const to = str(v.to)
    const subject = str(v.subject)
    const body = str(v.body)
    if (!to || !subject || !body) return '# 补全收件人/主题/正文后自动生成代码'
    return `"""邮件构造 → .eml。"""
from email.mime.text import MIMEText
from email.utils import formatdate

msg = MIMEText(${JSON.stringify(body)}, "plain", "utf-8")
msg["To"] = ${JSON.stringify(to)}
msg["Subject"] = ${JSON.stringify(subject)}
msg["Date"] = formatdate(localtime=True)
with open("draft.eml", "w", encoding="utf-8") as f:
    f.write(msg.as_string())
print("已输出 draft.eml")
${MARK}
import json as _json
print(_json.dumps({"rows": [{"label": "收件人", "value": ${JSON.stringify(to)}}, {"label": "主题", "value": ${JSON.stringify(subject)}}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const W12_SCHEMAS: InteractiveToolSchema[] = [
  charMatrixSchema,
  textTableSchema,
  siteMonitorSchema,
  fileWatchSchema,
  excelBuildSchema,
  excelStyleSchema,
  excelFormulaSchema,
  excelChartSchema,
  excelFreezeSchema,
  excelCondFmtSchema,
  excelSortSchema,
  excelProtectSchema,
  excelCommentSchema,
  excelMergeHeaderSchema,
  wordDocSchema,
  wordTableSchema,
  wordLettersSchema,
  pptSlidesSchema,
  dailyReportSchema,
  mdTodoSchema,
  mailDraftSchema
]
