// tool-schemas-w14.ts：W14 终局补齐 ×12——最后一批「无任何交互页面」的目录工具。
// 危险操作（粉碎/轮转删除/同步覆盖/清理）一律「预览 → 显式 apply」两步语义。
// 依赖：标准库（hashlib/zipfile/tarfile/subprocess/sqlite3），零第三方。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const MARK = 'print("<<<JSON>>>")'

// ---------------------------------------------------------------------------
// 1. 哈希校验器（文件多算法校验和）
// ---------------------------------------------------------------------------
export const hashCheckerSchema: InteractiveToolSchema = {
  id: 'interactive:hash-checker',
  title: '哈希校验器',
  description: '文件校验和：MD5/SHA1/SHA256 一次算全（hashlib，流式读取大文件友好）。',
  tags: ['安全', '文件'],
  fields: [{ key: 'file', label: '文件', type: 'file', required: true }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '文件', value: str(v.file), copy: true }] } : { error: '请选择文件' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择文件后自动生成代码'
    return `"""哈希校验和（流式读取）。"""
import hashlib
import json

algos = ["md5", "sha1", "sha256"]
digests = {name: hashlib.new(name) for name in algos}
with open(${JSON.stringify(file)}, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        for h in digests.values():
            h.update(chunk)
rows = [[name.upper(), h.hexdigest()] for name, h in digests.items()]
print("<<<JSON>>>")
print(json.dumps({"table": {"columns": ["算法", "校验和"], "rows": rows}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 2. 网页正文提取（剥脚本/样式/标签的阅读器思路）
// ---------------------------------------------------------------------------
export const webArticleSchema: InteractiveToolSchema = {
  id: 'interactive:web-article',
  title: '网页正文提取',
  description: 'URL → 剥离 script/style 后的正文文本（标准库 html.parser 思路；需联网）。',
  tags: ['网络'],
  fields: [{ key: 'url', label: 'URL', type: 'text', required: true, placeholder: 'https://example.com/article' }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.url) ? { rows: [{ label: 'URL', value: str(v.url), copy: true }] } : { error: '请输入 URL' }),
  pyCode: (v) => {
    const url = str(v.url).trim()
    if (!url) return '# 输入 URL 后自动生成代码'
    return `"""网页正文提取（去 script/style，剥标签）。"""
import json
import re

import requests

html = requests.get(${JSON.stringify(url)}, timeout=15).text
html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\\1>", "", html)
text = re.sub(r"(?s)<[^>]+>", "\\n", html)
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
body = "\\n".join(lines)
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(body)), "unit": "字符"},
                  "text": body[:6000]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 3. 统一压缩解压器（向导：压缩 dir→zip / 解压 zip→工作区）
// ---------------------------------------------------------------------------
export const archiveToolSchema: InteractiveToolSchema = {
  id: 'interactive:archive-tool',
  title: '统一压缩解压器',
  description: '目录 → zip 压缩包，或 zip → 解压到运行工作区（zipfile，自动按扩展分派）。',
  tags: ['文件', '向导'],
  fields: [
    {
      key: 'direction',
      label: '方向',
      type: 'select',
      default: 'compress',
      width: 'half',
      options: [
        { value: 'compress', label: '压缩目录' },
        { value: 'extract', label: '解压 zip' }
      ]
    },
    { key: 'dir', label: '要压缩的目录', type: 'dir', required: false },
    { key: 'zip', label: 'zip 文件', type: 'file', required: false, accept: ['zip'] }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '方向与源', keys: ['direction', 'dir', 'zip'] },
    { title: '执行', keys: [] }
  ],
  compute: (v) => {
    if (str(v.direction ?? 'compress') === 'compress') {
      return str(v.dir)
        ? { rows: [{ label: '源目录', value: str(v.dir), copy: true }] }
        : { error: '请选择要压缩的目录' }
    }
    return str(v.zip) ? { rows: [{ label: '压缩包', value: str(v.zip), copy: true }] } : { error: '请选择 zip 文件' }
  },
  pyCode: (v) => {
    if (str(v.direction ?? 'compress') === 'compress') {
      const dir = str(v.dir)
      if (!dir) return '# 选择目录后自动生成代码'
      return `"""压缩目录 → backup.zip。"""
import json
import os
import zipfile

SRC = ${JSON.stringify(dir)}
count = 0
with zipfile.ZipFile("backup.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    for base, _dirs, files in os.walk(SRC):
        for f in files:
            full = os.path.join(base, f)
            zf.write(full, os.path.relpath(full, SRC))
            count += 1
size = os.path.getsize("backup.zip") / 1024
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "backup.zip"},
                           {"label": "规模", "value": f"{count} 个文件 / {size:.0f} KiB"}]}, ensure_ascii=False))
print("<<<END>>>")
`
    }
    const zip = str(v.zip)
    if (!zip) return '# 选择 zip 后自动生成代码'
    return `"""解压 zip → 运行工作区。"""
import json
import zipfile

with zipfile.ZipFile(${JSON.stringify(zip)}) as zf:
    names = zf.namelist()
    zf.extractall(".")
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(names)), "unit": "个文件已解压"}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 4. 临时文件清理器（向导：预览 → apply 删除）
// ---------------------------------------------------------------------------
export const tempCleanerSchema: InteractiveToolSchema = {
  id: 'interactive:temp-cleaner',
  title: '临时文件清理器',
  description: '清理 N 天前未修改的文件：默认预览（个数/可释放体积），勾选「执行」才删除。',
  tags: ['文件', '向导'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    { key: 'days', label: '天数', type: 'number', default: 7, width: 'half', help: '清理 mtime 早于 N 天的文件' },
    { key: 'apply', label: '执行删除', type: 'checkbox', help: '不勾选 = 只预览（安全默认）' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '规则', keys: ['dir', 'days'] },
    { title: '预览并执行', keys: ['apply'] }
  ],
  compute: (v) => {
    if (!str(v.dir)) return { error: '请选择目录' }
    const days = Math.trunc(Number(v.days ?? 7))
    if (!Number.isFinite(days) || days < 1) return { error: '天数需为 ≥1 的整数' }
    return {
      rows: [
        { label: '目录', value: str(v.dir), copy: true },
        { label: '规则', value: `mtime 早于 ${days} 天前` }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const days = Math.trunc(Number(v.days ?? 7))
    if (!dir || !Number.isFinite(days) || days < 1) return '# 选择目录后自动生成代码'
    return `"""临时文件清理（${v.apply === true ? '已勾选执行' : '预览模式'}）。"""
import json
import os
import time
from pathlib import Path

cutoff = time.time() - ${days} * 86400
targets = [p for p in Path(${JSON.stringify(dir)}).rglob("*") if p.is_file() and p.stat().st_mtime < cutoff]
freed = sum(p.stat().st_size for p in targets)
if ${v.apply === true ? 'True' : 'False'}:
    for p in targets:
        p.unlink()
    status = "已删除"
else:
    status = "预览模式（未删除）"
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(targets)), "unit": f"个文件 {status}"},
                  "rows": [{"label": "可释放", "value": f"{freed / 1024:.0f} KiB"}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 5. 目录打包备份（时间戳 zip）
// ---------------------------------------------------------------------------
export const dirBackupSchema: InteractiveToolSchema = {
  id: 'interactive:dir-backup',
  title: '目录打包备份',
  description: '目录 → 时间戳命名的 zip 备份（保留相对路径，产物在工作区）。',
  tags: ['文件'],
  fields: [{ key: 'dir', label: '目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""目录打包备份（时间戳命名）。"""
import json
import os
import time
import zipfile

stamp = time.strftime("%Y%m%d-%H%M%S")
out = f"backup-{stamp}.zip"
count = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for base, _dirs, files in os.walk(${JSON.stringify(dir)}):
        for f in files:
            full = os.path.join(base, f)
            zf.write(full, os.path.relpath(full, ${JSON.stringify(dir)}))
            count += 1
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": out, "copy": True},
                           {"label": "规模", "value": f"{count} 个文件"}]}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 6. 日志轮转（文件超限 → 轮转报告 + apply）
// ---------------------------------------------------------------------------
export const logRotateSchema: InteractiveToolSchema = {
  id: 'interactive:log-rotate',
  title: '日志轮转',
  description: '日志文件超过阈值 MB → 轮转为 .1 副本并清空原文件（默认预览，勾选执行）。',
  tags: ['文件', '向导'],
  fields: [
    { key: 'file', label: '日志文件', type: 'file', required: true, accept: ['log', 'txt', 'out'] },
    { key: 'maxMb', label: '阈值 MB', type: 'number', default: 10, width: 'half' },
    { key: 'apply', label: '执行轮转', type: 'checkbox', help: '不勾选 = 只报告是否需要轮转' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '阈值', keys: ['file', 'maxMb'] },
    { title: '预览并执行', keys: ['apply'] }
  ],
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择日志文件' }
    const mb = Number(v.maxMb ?? 10)
    if (!Number.isFinite(mb) || mb <= 0) return { error: '阈值需为正数（MB）' }
    return {
      rows: [
        { label: '文件', value: str(v.file), copy: true },
        { label: '阈值', value: `${mb} MB` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const mb = Number(v.maxMb ?? 10)
    if (!file || !Number.isFinite(mb) || mb <= 0) return '# 选择文件后自动生成代码'
    return `"""日志轮转（${v.apply === true ? '已勾选执行' : '预览模式'}）。"""
import json
import os
import shutil

size = os.path.getsize(${JSON.stringify(file)}) if os.path.exists(${JSON.stringify(file)}) else 0
need = size > ${mb} * 1024 * 1024
if need and ${v.apply === true ? 'True' : 'False'}:
    shutil.copy2(${JSON.stringify(file)}, ${JSON.stringify(file)} + ".1")
    open(${JSON.stringify(file)}, "w").close()
    status = "已轮转（原文件存为 .1，原文件已清空）"
elif need:
    status = "需要轮转（预览模式，未改动）"
else:
    status = "未达阈值，无需轮转"
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": f"{size / 1024 / 1024:.1f}", "unit": "MB"},
                  "rows": [{"label": "状态", "value": status}]}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 7. 目录同步器（向导：计划 → apply 复制）
// ---------------------------------------------------------------------------
export const dirSyncSchema: InteractiveToolSchema = {
  id: 'interactive:dir-sync',
  title: '目录同步器',
  description: 'rsync 精简版：按（相对路径, 大小, mtime）把源目录增量复制到目标（默认预览计划，勾选执行）。',
  tags: ['文件', '向导'],
  fields: [
    { key: 'src', label: '源目录', type: 'dir', required: true },
    { key: 'dst', label: '目标目录', type: 'dir', required: true },
    { key: 'apply', label: '执行同步', type: 'checkbox', help: '不勾选 = 只预览计划' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '源与目标', keys: ['src', 'dst'] },
    { title: '预览并执行', keys: ['apply'] }
  ],
  compute: (v) =>
    str(v.src) && str(v.dst)
      ? {
          rows: [
            { label: '源', value: str(v.src), copy: true },
            { label: '目标', value: str(v.dst), copy: true }
          ]
        }
      : { error: '请选择源与目标目录' },
  pyCode: (v) => {
    const src = str(v.src)
    const dst = str(v.dst)
    if (!src || !dst) return '# 选择源与目标目录后自动生成代码'
    return `"""目录同步（增量：相对路径不存在或 mtime/大小不同才复制）。"""
import json
import os
import shutil
from pathlib import Path

src, dst = Path(${JSON.stringify(src)}), Path(${JSON.stringify(dst)})
plan = []
for f in src.rglob("*"):
    if not f.is_file():
        continue
    rel = f.relative_to(src)
    target = dst / rel
    if not target.exists() or (f.stat().st_mtime, f.stat().st_size) != (target.stat().st_mtime, target.stat().st_size):
        plan.append((f, target))
if ${v.apply === true ? 'True' : 'False'}:
    for f, t in plan:
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, t)
    status = "已同步"
else:
    status = "预览模式（未复制）"
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(plan)), "unit": f"个文件 {status}"},
                  "table": {"columns": ["动作", "相对路径"], "rows": [["复制", str(t.relative_to(dst))] for _, t in plan[:100]]}},
                 ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 8. 敏感文件粉碎器（覆写多次后删除；需显式输入「粉碎」确认词）
// ---------------------------------------------------------------------------
export const fileShredderSchema: InteractiveToolSchema = {
  id: 'interactive:file-shredder',
  title: '敏感文件粉碎器',
  description: '⚠️ 不可逆：随机覆写 N 遍后删除文件。必须在确认框输入「粉碎」两字才会执行。',
  tags: ['安全', '向导'],
  fields: [
    { key: 'file', label: '目标文件', type: 'file', required: true },
    { key: 'passes', label: '覆写遍数', type: 'number', default: 3, width: 'half', help: '1~7' },
    { key: 'confirm', label: '输入「粉碎」确认', type: 'text', required: true, width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择文件与遍数', keys: ['file', 'passes'] },
    { title: '确认并执行', keys: ['confirm'] }
  ],
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择目标文件' }
    const passes = Math.trunc(Number(v.passes ?? 3))
    if (!Number.isFinite(passes) || passes < 1 || passes > 7) return { error: '覆写遍数需为 1~7 的整数' }
    if (str(v.confirm) !== '粉碎') return { error: '请在确认框输入「粉碎」两字' }
    return {
      rows: [
        { label: '目标', value: str(v.file), copy: true },
        { label: '覆写', value: `${passes} 遍随机数据` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const passes = Math.trunc(Number(v.passes ?? 3))
    if (!file || str(v.confirm) !== '粉碎' || !Number.isFinite(passes) || passes < 1)
      return '# 文件不可逆操作：请填写确认词「粉碎」'
    return `"""敏感文件粉碎：覆写 ${passes} 遍后删除（不可逆）。"""
import json
import os
import secrets

target = ${JSON.stringify(file)}
size = os.path.getsize(target)
with open(target, "r+b") as f:
    for _ in range(${passes}):
        f.seek(0)
        f.write(secrets.token_bytes(size))
    f.flush()
    os.fsync(f.fileno())
os.remove(target)
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": "已粉碎"},
                  "rows": [{"label": "原大小", "value": f"{size / 1024:.0f} KiB"},
                           {"label": "覆写", "value": "${passes} 遍后删除"}]}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 9. Word 插入图片（docx + image → 文末插图）
// ---------------------------------------------------------------------------
export const wordImageSchema: InteractiveToolSchema = {
  id: 'interactive:word-image',
  title: 'Word 插入图片',
  description: '把图片插入 docx 文档末尾（可设宽度英寸），产物在工作区。',
  tags: ['Word'],
  fields: [
    { key: 'doc', label: 'docx 文档', type: 'file', required: true, accept: ['docx'] },
    { key: 'image', label: '图片', type: 'file', required: true, accept: ['png', 'jpg', 'jpeg'] },
    { key: 'widthInch', label: '宽度(英寸)', type: 'number', default: 5, width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选择文档与图片', keys: ['doc', 'image'] },
    { title: '插入', keys: ['widthInch'] }
  ],
  compute: (v) =>
    str(v.doc) && str(v.image)
      ? {
          rows: [
            { label: '文档', value: str(v.doc), copy: true },
            { label: '图片', value: str(v.image), copy: true }
          ]
        }
      : { error: '请选择文档与图片' },
  pyCode: (v) => {
    const doc = str(v.doc)
    const image = str(v.image)
    const w = Number(v.widthInch ?? 5)
    if (!doc || !image || !Number.isFinite(w) || w <= 0) return '# 选择文档与图片后自动生成代码'
    return `"""docx 插入图片（宽 ${Number.isFinite(w) && w > 0 ? w : 5} 英寸）。"""
from docx import Document
from docx.shared import Inches

doc = Document(${JSON.stringify(doc)})
doc.add_picture(${JSON.stringify(image)}, width=Inches(${Number.isFinite(w) && w > 0 ? w : 5}))
doc.save("with_image.docx")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "with_image.docx"}]}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 10. PPT 数据表（CSV → 表格片）
// ---------------------------------------------------------------------------
export const pptDataTableSchema: InteractiveToolSchema = {
  id: 'interactive:ppt-data-table',
  title: 'PPT 数据表',
  description: 'CSV 数据 → 含表格的 pptx 片（首行表头，自动行列规模）。',
  tags: ['PPT'],
  fields: [
    {
      key: 'data',
      label: '数据（CSV，首行表头）',
      type: 'textarea',
      required: true,
      placeholder: '季度,销售额\nQ1,120'
    }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.data).trim() ? { rows: [{ label: '产物', value: 'data_table.pptx' }] } : { error: '请粘贴数据' },
  pyCode: (v) => {
    const data = str(v.data)
    if (!data.trim()) return '# 粘贴数据后自动生成代码'
    return `"""CSV → pptx 数据表片。"""
import csv
import io

from pptx import Presentation
from pptx.util import Inches

rows = list(csv.reader(io.StringIO(${JSON.stringify(data)})))
pres = Presentation()
slide = pres.slides.add_slide(pres.slide_layouts[5])
gt = slide.shapes.add_table(len(rows), len(rows[0]), Inches(0.8), Inches(1.5), Inches(8), Inches(0.8 + 0.4 * len(rows)))
tbl = gt.table
for i, row in enumerate(rows):
    for j, cell in enumerate(row):
        tbl.cell(i, j).text = str(cell)
pres.save("data_table.pptx")
${MARK}
import json as _json
print(_json.dumps({"rows": [{"label": "产物", "value": "data_table.pptx"},
                            {"label": "规模", "value": f"{len(rows)} 行 x {len(rows[0])} 列"}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 11-12. 花销记账（SQLite：月度汇总 / 记一笔）
// ---------------------------------------------------------------------------
export const expenseSummarySchema: InteractiveToolSchema = {
  id: 'interactive:expense-summary',
  title: '花销月度汇总',
  description: '读记账 SQLite 库（expenses 表：date/category/amount）→ 指定月份分类汇总表。',
  tags: ['数据库', '统计'],
  fields: [
    { key: 'db', label: '记账库文件', type: 'file', required: true, accept: ['db', 'sqlite', 'sqlite3'] },
    { key: 'month', label: '月份（YYYY-MM）', type: 'text', required: true, placeholder: '2026-10', width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选库', keys: ['db'] },
    { title: '汇总', keys: ['month'] }
  ],
  compute: (v) =>
    str(v.db) && str(v.month)
      ? {
          rows: [
            { label: '库文件', value: str(v.db), copy: true },
            { label: '月份', value: str(v.month) }
          ]
        }
      : { error: '请补全库文件与月份' },
  pyCode: (v) => {
    const db = str(v.db)
    const month = str(v.month)
    if (!db || !/^\d{4}-\d{2}$/.test(month)) return '# 补全库文件与月份后自动生成代码'
    return `"""花销月度汇总：${month}。"""
import json
import sqlite3
from collections import defaultdict

conn = sqlite3.connect(${JSON.stringify(db)})
rows = conn.execute("SELECT category, amount FROM expenses WHERE substr(date, 1, 7) = ?", (${JSON.stringify(month)},)).fetchall()
conn.close()
sums: dict = defaultdict(float)
for cat, amt in rows:
    sums[cat] += amt
table_rows = [[cat, f"{v:.2f}"] for cat, v in sorted(sums.items(), key=lambda kv: -kv[1])]
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": f"{sum(sums.values()):.2f}", "unit": "总支出"},
                  "table": {"columns": ["分类", "金额"], "rows": table_rows}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

export const expenseAddSchema: InteractiveToolSchema = {
  id: 'interactive:expense-add',
  title: '花销记一笔',
  description: '向记账 SQLite 库（expenses 表：date/category/amount/note）追加一笔，立即生效。',
  tags: ['数据库'],
  fields: [
    { key: 'db', label: '记账库文件', type: 'file', required: true, accept: ['db', 'sqlite', 'sqlite3'] },
    { key: 'date', label: '日期', type: 'text', required: true, placeholder: '2026-10-03', width: 'half' },
    { key: 'category', label: '分类', type: 'text', required: true, placeholder: '餐饮', width: 'half' },
    { key: 'amount', label: '金额', type: 'number', required: true, width: 'half' },
    { key: 'note', label: '备注', type: 'text', required: false, width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '选库', keys: ['db'] },
    { title: '记一笔', keys: ['date', 'category', 'amount', 'note'] }
  ],
  compute: (v) => {
    if (!str(v.db)) return { error: '请选择记账库文件' }
    if (!str(v.date) || !str(v.category) || v.amount === undefined) return { error: '请补全日期/分类/金额' }
    const n = Number(v.amount)
    if (!Number.isFinite(n) || n <= 0) return { error: '金额需为正数' }
    return {
      rows: [
        { label: '日期', value: str(v.date) },
        { label: '分类', value: str(v.category) },
        { label: '金额', value: str(n) }
      ]
    }
  },
  pyCode: (v) => {
    const db = str(v.db)
    const date = str(v.date)
    const cat = str(v.category)
    const amt = Number(v.amount)
    const note = str(v.note)
    if (!db || !date || !cat || !Number.isFinite(amt) || amt <= 0) return '# 补全库文件/日期/分类/金额后自动生成代码'
    return `"""记账：${date} ${cat} ${amt} 元。"""
import json
import sqlite3

conn = sqlite3.connect(${JSON.stringify(db)})
conn.execute("INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
             (${JSON.stringify(date)}, ${JSON.stringify(cat)}, ${amt}, ${JSON.stringify(note)}))
conn.commit()
total = conn.execute("SELECT SUM(amount) FROM expenses WHERE substr(date, 1, 7) = ?", (${JSON.stringify(date.slice(0, 7))},)).fetchone()[0]
conn.close()
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "已记账", "value": f"{cat} {amt:.2f} 元"},
                           {"label": "本月累计", "value": f"{total:.2f} 元"}]}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

export const W14_SCHEMAS: InteractiveToolSchema[] = [
  hashCheckerSchema,
  webArticleSchema,
  archiveToolSchema,
  tempCleanerSchema,
  dirBackupSchema,
  logRotateSchema,
  dirSyncSchema,
  fileShredderSchema,
  wordImageSchema,
  pptDataTableSchema,
  expenseSummarySchema,
  expenseAddSchema
]
