// tool-schemas-wizard.ts：W10 向导 ×6（多步表单 + sidecar 真实执行；「会改文件」的操作
// 一律显式 apply 开关，默认只预览——预览/执行两步语义与原 CLI 一致）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const MARK = 'print("<<<JSON>>>")'

const XLSX_ROWS = `from openpyxl import load_workbook

def sheet_rows(path, sheet=None):
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    rows = [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    return rows

`

// ---------------------------------------------------------------------------
// 1. 两表对比（键列 → 新增/移除）
// ---------------------------------------------------------------------------
export const tableDiffSchema: InteractiveToolSchema = {
  id: 'interactive:table-diff',
  title: '两表对比',
  description: '选两份工作簿 + 键列 → 新增/移除名单（教学示例的真实文件版）。',
  tags: ['Excel', '向导'],
  fields: [
    { key: 'oldFile', label: '旧表', type: 'file', required: true, accept: ['xlsx', 'xlsm'] },
    { key: 'newFile', label: '新表', type: 'file', required: true, accept: ['xlsx', 'xlsm'] },
    { key: 'keyCol', label: '键列表头', type: 'text', required: true, placeholder: '如：工号', width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择两表', keys: ['oldFile', 'newFile'] },
    { title: '键列与执行', keys: ['keyCol'] }
  ],
  compute: (v) =>
    str(v.oldFile) && str(v.newFile) && str(v.keyCol)
      ? {
          rows: [
            { label: '旧表', value: str(v.oldFile), copy: true },
            { label: '新表', value: str(v.newFile), copy: true }
          ]
        }
      : { error: '请按步骤补全两份工作簿与键列' },
  pyCode: (v) => {
    const o = str(v.oldFile)
    const n = str(v.newFile)
    const key = str(v.keyCol)
    if (!o || !n || !key) return '# 按步骤补全后自动生成代码'
    return `"""两表对比：以「${key}」为键的新增/移除名单。"""
import json

${XLSX_ROWS}
def to_dict(rows):
    head = rows[0]
    ki = head.index(${JSON.stringify(key)})
    return {r[ki]: r for r in rows[1:]}

old = to_dict(sheet_rows(${JSON.stringify(o)}))
new = to_dict(sheet_rows(${JSON.stringify(n)}))
added = [new[k] for k in new if k not in old]
removed = [old[k] for k in old if k not in new]
${MARK}
print(json.dumps({
    "primary": {"value": str(len(added)), "unit": "新增 / " + str(len(removed)) + " 移除"},
    "table": {"columns": ["变更", "明细"], "rows": [["新增", " | ".join(map(str, r))] for r in added[:50]]
              + [["移除", " | ".join(map(str, r))] for r in removed[:50]]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 2. 多 Sheet 拆分（报告形态）
// ---------------------------------------------------------------------------
export const sheetSplitSchema: InteractiveToolSchema = {
  id: 'interactive:sheet-split',
  title: '多 Sheet 拆分',
  description: '列出工作簿全部工作表与行列规模（拆分产物建议用「批量导出」类脚本落到目录）。',
  tags: ['Excel', '向导'],
  fields: [{ key: 'file', label: '工作簿', type: 'file', required: true, accept: ['xlsx', 'xlsm'] }],
  computeVia: 'sidecar',
  steps: [{ title: '选择工作簿', keys: ['file'] }],
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '工作簿', value: str(v.file), copy: true }] } : { error: '请选择工作簿' },
  pyCode: (v) => {
    const f = str(v.file)
    if (!f) return '# 选择工作簿后自动生成代码'
    return `"""多 Sheet 规模报告。"""
import json

from openpyxl import load_workbook

wb = load_workbook(${JSON.stringify(f)}, read_only=True)
rows = [[name, str(ws.max_row - 1), str(ws.max_column)] for name, ws in ((n, wb[n]) for n in wb.sheetnames)]
wb.close()
${MARK}
print(json.dumps({"table": {"columns": ["工作表", "数据行", "列数"], "rows": rows}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 3. Excel 去重合并
// ---------------------------------------------------------------------------
export const dedupMergeSchema: InteractiveToolSchema = {
  id: 'interactive:dedup-merge',
  title: 'Excel 去重合并',
  description: '两份名单以键列合并去重（旧表优先），给出唯一条数与合并预览。',
  tags: ['Excel', '向导'],
  fields: [
    { key: 'fileA', label: '表 A（优先保留）', type: 'file', required: true, accept: ['xlsx'] },
    { key: 'fileB', label: '表 B', type: 'file', required: true, accept: ['xlsx'] },
    { key: 'keyCol', label: '键列表头', type: 'text', required: true, placeholder: '如：工号', width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择两表', keys: ['fileA', 'fileB'] },
    { title: '键列与执行', keys: ['keyCol'] }
  ],
  compute: (v) =>
    str(v.fileA) && str(v.fileB) && str(v.keyCol)
      ? {
          rows: [
            { label: '表 A', value: str(v.fileA), copy: true },
            { label: '表 B', value: str(v.fileB), copy: true }
          ]
        }
      : { error: '请按步骤补全两份名单与键列' },
  pyCode: (v) => {
    const a = str(v.fileA)
    const b = str(v.fileB)
    const key = str(v.keyCol)
    if (!a || !b || !key) return '# 按步骤补全后自动生成代码'
    return `"""去重合并：以「${key}」为键，A 表优先。"""
import json

${XLSX_ROWS}
def to_rows(path):
    rows = sheet_rows(path)
    return rows[0], rows[1:]

headA, bodyA = to_rows(${JSON.stringify(a)})
headB, bodyB = to_rows(${JSON.stringify(b)})
ki = headA.index(${JSON.stringify(key)})
merged = {r[ki]: r for r in bodyB}
for r in bodyA:
    merged[r[ki]] = r  # A 覆盖 B
unique = list(merged.values())
${MARK}
print(json.dumps({
    "primary": {"value": str(len(unique)), "unit": "条唯一记录"},
    "table": {"columns": headA, "rows": [[" | ".join(map(str, r))][:1][0] and [str(c) for c in r] for r in unique[:30]]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 4. 批量重命名（预览 → apply 两步）
// ---------------------------------------------------------------------------
export const batchRenameSchema: InteractiveToolSchema = {
  id: 'interactive:batch-rename',
  title: '批量重命名',
  description: '目录内文件按前缀+序号重命名：默认只预览改名计划，显式勾选「执行」才落盘。',
  tags: ['文件', '向导'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    { key: 'prefix', label: '新前缀', type: 'text', default: 'file', width: 'half' },
    { key: 'apply', label: '执行改名', type: 'checkbox', help: '不勾选 = 只预览计划（安全默认）' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '命名规则', keys: ['dir', 'prefix'] },
    { title: '预览并执行', keys: ['apply'] }
  ],
  compute: (v) =>
    str(v.dir)
      ? {
          rows: [
            { label: '目录', value: str(v.dir), copy: true },
            { label: '前缀', value: str(v.prefix ?? 'file') }
          ]
        }
      : { error: '请选择目录' },
  pyCode: (v) => {
    const dir = str(v.dir)
    const prefix = str(v.prefix ?? 'file')
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""批量重命名（默认预览；${v.apply === true ? '已勾选执行' : '未勾选执行——只预览'}）。"""
import json
from pathlib import Path

files = sorted(p for p in Path(${JSON.stringify(dir)}).iterdir() if p.is_file())
plan = [(p, p.with_name(f"${prefix}_{i:03d}{p.suffix}")) for i, p in enumerate(files, 1)]
${v.apply === true ? 'for old, new in plan:\n    old.rename(new)\nstatus = "已执行改名"' : 'status = "预览模式（未改名）"'}
${MARK}
print(json.dumps({
    "primary": {"value": str(len(plan)), "unit": "个文件 " + status},
    "table": {"columns": ["原文件", "新文件"], "rows": [[o.name, n.name] for o, n in plan[:60]]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 5. 文件自动分类（预览 → apply）
// ---------------------------------------------------------------------------
const CLASSIFY_MAP = {
  图片: ['png', 'jpg', 'jpeg', 'gif', 'webp'],
  文档: ['pdf', 'docx', 'doc', 'md', 'txt'],
  表格: ['xlsx', 'xlsm', 'csv'],
  音视频: ['mp4', 'mov', 'mp3', 'm4a'],
  压缩包: ['zip', 'tar', 'gz', '7z']
}

export const fileClassifySchema: InteractiveToolSchema = {
  id: 'interactive:file-classify',
  title: '文件自动分类',
  description: '按扩展名归类到子目录（图片/文档/表格/音视频/压缩包）：默认预览计划，勾选「执行」才移动。',
  tags: ['文件', '向导'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    { key: 'apply', label: '执行归类', type: 'checkbox', help: '不勾选 = 只预览计划（安全默认）' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择目录', keys: ['dir'] },
    { title: '预览并执行', keys: ['apply'] }
  ],
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""文件自动分类（${v.apply === true ? '已勾选执行' : '预览模式'}）。"""
import json
import shutil
from pathlib import Path

MAP = ${JSON.stringify(CLASSIFY_MAP)}
plan: list = []
for f in Path(${JSON.stringify(dir)}).iterdir():
    if not f.is_file():
        continue
    cat = next((c for c, exts in MAP.items() if f.suffix.lower().lstrip(".") in exts), "其他")
    plan.append((f, cat))
${v.apply === true ? 'for f, cat in plan:\n    dest = Path(f.parent) / cat\n    dest.mkdir(exist_ok=True)\n    shutil.move(str(f), str(dest / f.name))\nstatus = "已归类"' : 'status = "预览模式（未移动）"'}
${MARK}
print(json.dumps({
    "primary": {"value": str(len(plan)), "unit": "个文件 " + status},
    "table": {"columns": ["文件", "归类"], "rows": [[f.name, cat] for f, cat in plan[:60]]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 6. SQLite → Excel（方向一：读库出表预览 + 落 xlsx 到运行工作区）
// ---------------------------------------------------------------------------
export const sqliteExportSchema: InteractiveToolSchema = {
  id: 'interactive:sqlite-export',
  title: 'SQLite → Excel',
  description: '读 SQLite 库中指定表的全部行，落成 xlsx（运行工作区）并给出前 30 行预览。',
  tags: ['数据库', '向导'],
  fields: [
    { key: 'db', label: 'SQLite 库文件', type: 'file', required: true, accept: ['db', 'sqlite', 'sqlite3', 'db3'] },
    { key: 'table', label: '表名', type: 'text', required: true, placeholder: '如：orders', width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择库与表', keys: ['db', 'table'] },
    { title: '导出', keys: [] }
  ],
  compute: (v) =>
    str(v.db) && str(v.table)
      ? {
          rows: [
            { label: '库文件', value: str(v.db), copy: true },
            { label: '表', value: str(v.table) }
          ]
        }
      : { error: '请补全库文件与表名' },
  pyCode: (v) => {
    const db = str(v.db)
    const table = str(v.table)
    if (!db || !table) return '# 补全库文件与表名后自动生成代码'
    return `"""SQLite → Excel：表「${table}」全量导出。"""
import json
import sqlite3

import openpyxl

conn = sqlite3.connect(${JSON.stringify(db)})
cur = conn.execute('SELECT * FROM "${table}"')
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
wb = openpyxl.Workbook()
ws = wb.active
ws.append(cols)
for r in rows:
    ws.append(["" if c is None else c for c in r])
wb.save("exported.xlsx")
conn.close()
${MARK}
print(json.dumps({
    "primary": {"value": str(len(rows)), "unit": "行已导出 exported.xlsx"},
    "table": {"columns": cols, "rows": [[str(c) for c in r] for r in rows[:30]]},
}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const WIZARD_SCHEMAS: InteractiveToolSchema[] = [
  tableDiffSchema,
  sheetSplitSchema,
  dedupMergeSchema,
  batchRenameSchema,
  fileClassifySchema,
  sqliteExportSchema
]
