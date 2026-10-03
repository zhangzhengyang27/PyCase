// tool-schemas-results.ts：W9 结果浏览 ×13（文件系统/统计工具的结构化表格化）。
// 形态：dir/file 字段 + pyCode 产 JSON 表格 → 页面表格渲染。
// 「只报告不删改」的工具保持原语义（删除/移动类操作在向导工具里显式 apply）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')

const TABLE = (columns: string, rowsExpr: string) => `print("<<<JSON>>>")
print(json.dumps({"table": {"columns": ${columns}, "rows": ${rowsExpr}}}, ensure_ascii=False))
print("<<<END>>>")
`

// 人类可读体积（多处复用）
const HUMAN = `def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"
`

// ---------------------------------------------------------------------------
// 1. 大文件 TopN
// ---------------------------------------------------------------------------
export const bigFileSchema: InteractiveToolSchema = {
  id: 'interactive:bigfile-topn',
  title: '大文件 TopN',
  description: '递归找出目录下最大的 N 个文件（体积人类可读，表格呈现）。',
  tags: ['文件', '结果浏览'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    { key: 'top', label: 'N', type: 'number', default: 10, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.dir)) return { error: '请选择目录' }
    const top = Math.trunc(Number(v.top ?? 10))
    if (!Number.isFinite(top) || top < 1 || top > 200) return { error: 'N 需为 1~200 的整数' }
    return {
      rows: [
        { label: '目录', value: str(v.dir), copy: true },
        { label: 'Top', value: String(top) }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const top = Math.trunc(Number(v.top ?? 10))
    if (!dir || !Number.isFinite(top) || top < 1) return '# 选择目录后自动生成代码'
    return `"""大文件 TopN（只报告，不做任何删改）。"""
import json
${HUMAN}
files = [(f.stat().st_size, f) for f in __import__("pathlib").Path(${JSON.stringify(dir)}).rglob("*") if f.is_file()]
files.sort(reverse=True)
${TABLE('["体积", "路径"]', `[[human(s), str(p)] for s, p in files[:${top}]]`)}`
  }
}

// ---------------------------------------------------------------------------
// 2. 重复文件查找（清理器的报告形态：只报告组，不做删除）
// ---------------------------------------------------------------------------
export const duplicateFinderSchema: InteractiveToolSchema = {
  id: 'interactive:dup-finder',
  title: '重复文件查找',
  description: '按（体积, 内容哈希前 8KB）分组找重复文件，组号呈现；只报告不删除。',
  tags: ['文件', '结果浏览'],
  fields: [{ key: 'dir', label: '目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""重复文件查找（内容哈希分组；只报告不删除）。"""
import hashlib
import json
${HUMAN}
from pathlib import Path

groups: dict = {}
for f in Path(${JSON.stringify(dir)}).rglob("*"):
    if not f.is_file():
        continue
    try:
        size = f.stat().st_size
        with f.open("rb") as fh:
            digest = hashlib.md5(fh.read(8192)).hexdigest()
        groups.setdefault((size, digest), []).append(str(f))
    except OSError:
        continue
dups = [paths for _, paths in groups.items() if len(paths) > 1]
rows = []
for gi, paths in enumerate(dups, 1):
    for p in paths:
        rows.append([f"#{gi}", HUMAN(Path(p).stat().st_size), p])
${TABLE('["组", "体积", "路径"]', 'rows')}`
  }
}

// ---------------------------------------------------------------------------
// 3. 空目录报告
// ---------------------------------------------------------------------------
export const emptyDirSchema: InteractiveToolSchema = {
  id: 'interactive:empty-dir',
  title: '空目录报告',
  description: '递归列出全部空目录（自底向上；只报告不删除）。',
  tags: ['文件', '结果浏览'],
  fields: [{ key: 'dir', label: '目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""空目录报告（只报告不删除）。"""
import json
from pathlib import Path

empties = [str(p) for p in sorted(Path(${JSON.stringify(dir)}).rglob("*"), reverse=True)
           if p.is_dir() and not any(p.iterdir())]
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(empties)), "unit": "个空目录"},
                  "table": {"columns": ["空目录"], "rows": [[p] for p in empties[:200]]}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 4. 目录体积报告
// ---------------------------------------------------------------------------
export const dirSizeSchema: InteractiveToolSchema = {
  id: 'interactive:dir-size',
  title: '目录体积报告',
  description: '一级子目录与直属文件的体积排行（人类可读，降序）。',
  tags: ['文件', '结果浏览'],
  fields: [{ key: 'dir', label: '目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""目录体积报告。"""
import json
${HUMAN}
from pathlib import Path

def tree_size(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    total = 0
    for c in p.iterdir():
        try:
            total += tree_size(c) if c.is_dir() else (c.stat().st_size if c.is_file() else 0)
        except OSError:
            pass
    return total

base = Path(${JSON.stringify(dir)})
entries = [(tree_size(c), c) for c in base.iterdir()]
entries.sort(reverse=True)
${TABLE('["体积", "名称"]', `[[human(s), c.name + ("/" if c.is_dir() else "")] for s, c in entries[:50]]`)}`
  }
}

// ---------------------------------------------------------------------------
// 5. 快速文件查找
// ---------------------------------------------------------------------------
export const quickFindSchema: InteractiveToolSchema = {
  id: 'interactive:quick-find',
  title: '快速文件查找',
  description: '按文件名正则递归搜索（fd 精简版），表格呈现路径与体积。',
  tags: ['文件', '结果浏览'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    { key: 'pattern', label: '文件名正则', type: 'text', required: true, placeholder: 'report.*\\.xlsx' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.dir) && str(v.pattern)
      ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] }
      : { error: '请补全目录与正则' },
  pyCode: (v) => {
    const dir = str(v.dir)
    const pattern = str(v.pattern)
    if (!dir || !pattern) return '# 补全目录与正则后自动生成代码'
    return `"""快速文件查找（名称正则；正则为 Python 方言）。"""
import json
import re
${HUMAN}
from pathlib import Path

pat = re.compile(r'''${pattern}''', re.I)
hits = [(f.stat().st_size, f) for f in Path(${JSON.stringify(dir)}).rglob("*") if f.is_file() and pat.search(f.name)]
hits.sort(reverse=True)
${TABLE('["体积", "路径"]', '[[HUMAN(s), str(p)] for s, p in hits[:100]]')}`
  }
}

// ---------------------------------------------------------------------------
// 6. 目录树打印
// ---------------------------------------------------------------------------
export const treePrintSchema: InteractiveToolSchema = {
  id: 'interactive:tree-print',
  title: '目录树打印',
  description: 'tree 命令的 Python 版：指定深度打印目录树（忽略 .git/node_modules 等）。',
  tags: ['文件'],
  fields: [
    { key: 'dir', label: '目录', type: 'dir', required: true },
    { key: 'depth', label: '深度', type: 'number', default: 3, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.dir)) return { error: '请选择目录' }
    const depth = Math.trunc(Number(v.depth ?? 3))
    if (!Number.isFinite(depth) || depth < 1 || depth > 8) return { error: '深度需为 1~8 的整数' }
    return { rows: [{ label: '目录', value: str(v.dir), copy: true }] }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const depth = Math.trunc(Number(v.depth ?? 3))
    if (!dir || !Number.isFinite(depth) || depth < 1) return '# 选择目录后自动生成代码'
    return `"""目录树打印（深度 ${Number.isFinite(depth) ? depth : 3}）。"""
import json
from pathlib import Path

IGNORE = {".git", "node_modules", "__pycache__", ".venv"}
lines = []
def walk(p: Path, prefix: str, level: int):
    if level > ${Number.isFinite(depth) ? depth : 3}:
        return
    kids = sorted(p.iterdir(), key=lambda c: (c.is_file(), c.name))
    for c in kids:
        if c.name in IGNORE:
            continue
        lines.append(prefix + ("├── " if True else "") + c.name + ("/" if c.is_dir() else ""))
        if c.is_dir():
            walk(c, prefix + "│   ", level + 1)

base = Path(${JSON.stringify(dir)})
lines.append(base.name + "/")
walk(base, "", 1)
print("<<<JSON>>>")
print(json.dumps({"text": "\\n".join(lines[:400])}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 7-8. TODO 扫描 / 敏感信息扫描（同构：行正则扫描）
// ---------------------------------------------------------------------------
export const todoScanSchema: InteractiveToolSchema = {
  id: 'interactive:todo-scan',
  title: 'TODO/FIXME 扫描',
  description: '扫描目录下代码文件中的 TODO/FIXME/HACK 标记（表格：文件/行号/内容）。',
  tags: ['代码', '结果浏览'],
  fields: [{ key: 'dir', label: '代码目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""TODO/FIXME 扫描。"""
import json
import re
from pathlib import Path

pat = re.compile(r"(TODO|FIXME|HACK)[:：]?\\s*(.*)")
exts = {".py", ".ts", ".js", ".vue", ".md", ".go", ".rs", ".java"}
rows = []
for f in sorted(Path(${JSON.stringify(dir)}).rglob("*")):
    if f.suffix not in exts or not f.is_file():
        continue
    try:
        for i, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = pat.search(ln)
            if m:
                rows.append([str(f), str(i), f"{m.group(1)} {m.group(2)[:60]}"])
    except OSError:
        continue
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(rows)), "unit": "处标记"},
                  "table": {"columns": ["文件", "行", "标记"], "rows": rows[:200]}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

export const secretScanSchema: InteractiveToolSchema = {
  id: 'interactive:secret-scan',
  title: '敏感信息扫描',
  description: '扫描代码里的密钥/token 泄漏风险（api_key/secret/token 赋值模式；只报告不外发）。',
  tags: ['安全'],
  fields: [{ key: 'dir', label: '代码目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""敏感信息扫描（赋值模式启发式；值打码展示）。"""
import json
import re
from pathlib import Path

pat = re.compile(r"(api[_-]?key|secret|token|passwd|password)\\s*[=: ]\\s*["']([\\w-]{8,})[\\"']", re.I)
exts = {".py", ".ts", ".js", ".vue", ".env", ".json", ".yml", ".yaml"}
rows = []
for f in sorted(Path(${JSON.stringify(dir)}).rglob("*")):
    if f.suffix not in exts or not f.is_file():
        continue
    try:
        for i, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = pat.search(ln)
            if m:
                masked = m.group(2)[:3] + "***"
                rows.append([str(f), str(i), f"{m.group(1)} = {masked}"])
    except OSError:
        continue
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(rows)), "unit": "处疑似泄漏"},
                  "table": {"columns": ["文件", "行", "内容（打码）"], "rows": rows[:200]}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 9. 代码行数统计
// ---------------------------------------------------------------------------
export const locStatsSchema: InteractiveToolSchema = {
  id: 'interactive:loc-stats',
  title: '代码行数统计',
  description: 'cloc 精简版：按扩展名统计代码/注释/空行（# 与 // 两种注释口径）。',
  tags: ['代码', '统计'],
  fields: [{ key: 'dir', label: '代码目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择目录' }),
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择目录后自动生成代码'
    return `"""代码行数统计（按扩展名）。"""
import json
from pathlib import Path

stats: dict = {}
for f in Path(${JSON.stringify(dir)}).rglob("*"):
    if not f.is_file() or f.suffix not in {".py", ".ts", ".js", ".vue", ".md", ".go"}:
        continue
    code = comment = blank = 0
    for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = ln.strip()
        if not s:
            blank += 1
        elif s.startswith(("#", "//")):
            comment += 1
        else:
            code += 1
    acc = stats.setdefault(f.suffix, [0, 0, 0, 0])
    acc[0], acc[1], acc[2] = acc[0] + code, acc[1] + comment, acc[2] + blank
    acc[3] += 1
rows = [[ext, str(v[3]), str(v[0]), str(v[1]), str(v[2])] for ext, v in sorted(stats.items(), key=lambda kv: -kv[1][0])]
print("<<<JSON>>>")
print(json.dumps({"table": {"columns": ["扩展名", "文件数", "代码行", "注释行", "空行"], "rows": rows}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 10. CSV 列统计
// ---------------------------------------------------------------------------
export const csvStatsSchema: InteractiveToolSchema = {
  id: 'interactive:csv-column-stats',
  title: 'CSV 列统计',
  description: 'CSV 数值列速览：计数/均值/最小/最大（自动识别数值列）。',
  tags: ['CSV', '统计'],
  fields: [
    { key: 'file', label: 'CSV 文件', type: 'file', required: true, accept: ['csv'] },
    { key: 'column', label: '列名', type: 'text', required: true, placeholder: '数值列的表头名', width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) && str(v.column)
      ? { rows: [{ label: '文件', value: str(v.file), copy: true }] }
      : { error: '请补全文件与列名' },
  pyCode: (v) => {
    const file = str(v.file)
    const col = str(v.column)
    if (!file || !col) return '# 补全文件与列名后自动生成代码'
    return `"""CSV 列统计。"""
import csv
import json

vals = []
with open(${JSON.stringify(file)}, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            vals.append(float(row[${JSON.stringify(col)}]))
        except (KeyError, TypeError, ValueError):
            continue
if not vals:
    raise SystemExit("该列没有可统计的数值")
vals.sort()
mean = sum(vals) / len(vals)
_r = {
    "primary": {"value": f"{mean:.4g}", "unit": "均值"},
    "rows": [
        {"label": "计数", "value": str(len(vals))},
        {"label": "最小 / 最大", "value": f"{vals[0]:.4g} / {vals[-1]:.4g}"},
        {"label": "中位数", "value": f"{vals[len(vals) // 2]:.4g}"},
    ],
}
print("<<<JSON>>>")
print(json.dumps(_r, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 11. 日志等级统计
// ---------------------------------------------------------------------------
export const logLevelSchema: InteractiveToolSchema = {
  id: 'interactive:log-level-stats',
  title: '日志等级统计',
  description: '解析日志行的级别分布（INFO/WARN/ERROR…）+ 错误明细抽样。',
  tags: ['日志', '统计'],
  fields: [{ key: 'file', label: '日志文件', type: 'file', required: true, accept: ['log', 'txt', 'out'] }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '文件', value: str(v.file), copy: true }] } : { error: '请选择日志文件' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择日志文件后自动生成代码'
    return `"""日志等级统计。"""
import json
import re
from collections import Counter

pat = re.compile(r"\\b(TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\\b")
levels: Counter = Counter()
errors: list = []
for i, ln in enumerate(open(${JSON.stringify(file)}, encoding="utf-8", errors="ignore"), 1):
    m = pat.search(ln)
    if not m:
        continue
    levels[m.group(1).replace("WARNING", "WARN").replace("FATAL", "CRITICAL")] += 1
    if m.group(1) in ("ERROR", "CRITICAL", "FATAL") and len(errors) < 20:
        errors.append([str(i), ln.strip()[:120]])
rows = [[k, str(v)] for k, v in levels.most_common()]
print("<<<JSON>>>")
print(json.dumps({"table": {"columns": ["级别", "条数"], "rows": rows},
                  "text": ("错误明细抽样：\\n" + "\\n".join(f"L{i} {t}" for i, t in errors)) if errors else ""}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

// ---------------------------------------------------------------------------
// 12-13. Git 报告（依赖当前机器的 git 与所选仓库）
// ---------------------------------------------------------------------------
const GIT_PRELUDE = `import json
import subprocess

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, timeout=30, cwd=REPO).stdout

REPO = `

export const gitBranchSchema: InteractiveToolSchema = {
  id: 'interactive:git-branches',
  title: 'Git 分支报告',
  description: '本地/远程分支一览 + 当前分支（对所选仓库运行 git）。',
  tags: ['Git', '结果浏览'],
  fields: [{ key: 'dir', label: '仓库目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.dir) ? { rows: [{ label: '仓库', value: str(v.dir), copy: true }] } : { error: '请选择仓库目录' },
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择仓库目录后自动生成代码'
    return `"""Git 分支报告。"""
${GIT_PRELUDE} ${JSON.stringify(dir)}
current = git("rev-parse", "--abbrev-ref", "HEAD").strip()
branches = [b.strip() for b in git("branch", "--list").splitlines() if b.strip()]
rows = [("★ " + current if b.replace("* ", "") == current else b.replace("* ", "")) for b in branches]
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": current}, "list": rows}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

export const gitCommitSchema: InteractiveToolSchema = {
  id: 'interactive:git-commits',
  title: 'Git 提交统计',
  description: '按作者统计提交数与增删行（git log --numstat）。',
  tags: ['Git', '统计'],
  fields: [{ key: 'dir', label: '仓库目录', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.dir) ? { rows: [{ label: '仓库', value: str(v.dir), copy: true }] } : { error: '请选择仓库目录' },
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择仓库目录后自动生成代码'
    return `"""Git 提交统计。"""
${GIT_PRELUDE} ${JSON.stringify(dir)}
stats: dict = {}
author = None
for ln in git("log", "--numstat", "--format=%an").splitlines():
    if not ln.strip():
        author = None
    elif "\\t" not in ln:
        author = ln.strip()
    elif author:
        parts = ln.split("\\t")
        add, dele = parts[0], parts[1]
        acc = stats.setdefault(author, [0, 0, 0])
        acc[0] += 1
        acc[1] += int(add) if add.isdigit() else 0
        acc[2] += int(dele) if dele.isdigit() else 0
rows = [[a, str(s[0]), str(s[1]), str(s[2])] for a, s in sorted(stats.items(), key=lambda kv: -kv[1][0])]
print("<<<JSON>>>")
print(json.dumps({"table": {"columns": ["作者", "提交数", "新增行", "删除行"], "rows": rows}}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

export const RESULTS_SCHEMAS: InteractiveToolSchema[] = [
  bigFileSchema,
  duplicateFinderSchema,
  emptyDirSchema,
  dirSizeSchema,
  quickFindSchema,
  treePrintSchema,
  todoScanSchema,
  secretScanSchema,
  locStatsSchema,
  csvStatsSchema,
  logLevelSchema,
  gitBranchSchema,
  gitCommitSchema
]
