// tool-schemas-w15.ts：W15 终极补齐 ×3——密码保险库 / 一次性定时任务 / Word 读取。
// 此后 163 个工具中除 migrated 课程脚本与纯教学读取演示外全部有交互页面。
// 依赖：标准库（hashlib/sched/sqlite3 不需要）；docx 读取用 python-docx（已装）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const MARK = 'print("<<<JSON>>>")'

// ---------------------------------------------------------------------------
// 1. 密码保险库（教学级 keystream 加密：主口令+盐派生流；页面驱动 add/list）
//    安全声明沿用原工具：教学级实现，生产请用 keyring/1Password。
// ---------------------------------------------------------------------------
const VAULT_LIB = `import base64
import hashlib
import json
import os

VAULT = "vault.enc.json"

def keystream(master, salt, size):
    out = b""
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(master.encode() + salt + str(counter).encode()).digest()
        counter += 1
    return out[:size]

def xor(data, key):
    return bytes(a ^ b for a, b in zip(data, key))

def load(master):
    raw = json.loads(open(VAULT, encoding="utf-8").read())
    salt = base64.b64decode(raw["salt"])
    data = xor(base64.b64decode(raw["data"]), keystream(master, salt, len(base64.b64decode(raw["data"]))))
    return json.loads(data.decode("utf-8"))

def save(master, entries):
    salt = os.urandom(16)
    text = json.dumps(entries, ensure_ascii=False).encode("utf-8")
    enc = xor(text, keystream(master, salt, len(text)))
    open(VAULT, "w", encoding="utf-8").write(json.dumps(
        {"salt": base64.b64encode(salt).decode(), "data": base64.b64encode(enc).decode()}))
`

export const vaultAddSchema: InteractiveToolSchema = {
  id: 'interactive:vault-add',
  title: '密码保险库',
  description:
    '⚠️ 教学级加密存储（主口令派生 keystream；生产请用 keyring/1Password）：新建/追加条目到 vault.enc.json，错误口令解出乱码即暴露。',
  tags: ['安全', '向导'],
  fields: [
    { key: 'master', label: '主口令', type: 'password', required: true, width: 'half' },
    { key: 'site', label: '站点/应用', type: 'text', required: true, placeholder: 'github.com', width: 'half' },
    { key: 'secret', label: '密码', type: 'password', required: true, width: 'half' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '条目', keys: ['master', 'site', 'secret'] },
    { title: '写入', keys: [] }
  ],
  compute: (v) =>
    str(v.master) && str(v.site) && str(v.secret)
      ? {
          rows: [
            { label: '站点', value: str(v.site) },
            { label: '库文件', value: 'vault.enc.json（工作区）' }
          ]
        }
      : { error: '请补全主口令/站点/密码' },
  pyCode: (v) => {
    const master = str(v.master)
    const site = str(v.site)
    const secret = str(v.secret)
    if (!master || !site || !secret) return '# 补全主口令/站点/密码后自动生成代码'
    return `"""密码保险库：新建或追加条目（教学级）。"""
${VAULT_LIB}
import sys

entries = {}
if os.path.exists(VAULT):
    try:
        entries = load(${JSON.stringify(master)})
    except Exception:
        print("解密失败：主口令错误或库已损坏")
        sys.exit(1)
entries[${JSON.stringify(site)}] = ${JSON.stringify(secret)}
save(${JSON.stringify(master)}, entries)
${MARK}
print(json.dumps({"primary": {"value": "已保存"},
                  "rows": [{"label": "站点", "value": ${JSON.stringify(site)}},
                           {"label": "库文件", "value": "vault.enc.json（已加密）"}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const vaultListSchema: InteractiveToolSchema = {
  ...vaultAddSchema,
  id: 'interactive:vault-list',
  title: '密码保险库查看',
  description: '用主口令解密 vault.enc.json 并列出全部站点（密码打码展示）。',
  tags: ['安全'],
  steps: undefined,
  fields: [{ key: 'master', label: '主口令', type: 'password', required: true }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.master) ? { rows: [{ label: '状态', value: '点击「运行」解密' }] } : { error: '请输入主口令' },
  pyCode: (v) => {
    const master = str(v.master)
    if (!master) return '# 输入主口令后自动生成代码'
    return `"""密码保险库：解密列出（教学级）。"""
${VAULT_LIB}
entries = load(${JSON.stringify(master)})
${MARK}
print(json.dumps({"list": [f"{site}  →  {pwd[:2]}{'*' * max(0, len(pwd) - 2)}" for site, pwd in entries.items()]},
                 ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 2. 一次性定时任务（页面内倒计时 → 到点经 sidecar 执行）
// ---------------------------------------------------------------------------
export const schedOnceSchema: InteractiveToolSchema = {
  id: 'interactive:sched-once',
  title: '一次性定时任务',
  description: '延时 N 秒后执行一段 Python 代码（sched 语义的页面版：倒计时期间可取消）。',
  tags: ['系统', '向导'],
  fields: [
    { key: 'delay', label: '延时(秒)', type: 'number', default: 5, width: 'half', help: '2~600' },
    { key: 'task', label: '要执行的 Python 代码', type: 'textarea', required: true, placeholder: "print('任务执行')" }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '任务与延时', keys: ['delay', 'task'] },
    { title: '定时执行', keys: [] }
  ],
  compute: (v) => {
    if (!str(v.task).trim()) return { error: '请输入要执行的代码' }
    const sec = Math.trunc(Number(v.delay ?? 5))
    if (!Number.isFinite(sec) || sec < 2 || sec > 600) return { error: '延时需为 2~600 秒' }
    return { rows: [{ label: '延时', value: `${sec} 秒` }] }
  },
  pyCode: (v) => {
    const task = str(v.task)
    const sec = Math.trunc(Number(v.delay ?? 5))
    if (!task.trim() || !Number.isFinite(sec) || sec < 2) return '# 补全延时与代码后自动生成'
    return `"""一次性定时任务：sched 延时 ${sec}s 执行。"""
import json
import sched
import time

scheduler = sched.scheduler(time.time, time.sleep)

def task():
${task
  .split('\n')
  .map((ln) => '    ' + ln)
  .join('\n')}

print("当前:", time.strftime("%H:%M:%S"))
scheduler.enter(${sec}, 1, task)
scheduler.run()
print("队列执行完毕")
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": "已执行"}, "rows": [{"label": "延时", "value": "${sec} 秒"}]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 3. Word 读取（docx → 段落/表格文本提取）
// ---------------------------------------------------------------------------
export const wordReadSchema: InteractiveToolSchema = {
  id: 'interactive:word-read',
  title: 'Word 读取',
  description: 'docx → 段落（带样式名）与表格内容提取（python-docx）。',
  tags: ['Word'],
  fields: [{ key: 'file', label: 'docx 文档', type: 'file', required: true, accept: ['docx'] }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '文档', value: str(v.file), copy: true }] } : { error: '请选择文档' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择文档后自动生成代码'
    return `"""Word 读取：段落 + 表格提取。"""
import json

from docx import Document

try:
    doc = Document(${JSON.stringify(file)})
except Exception as e:
    print("<<<JSON>>>")
    print(json.dumps({"error": f"文档读取失败: {e}"}, ensure_ascii=False))
    print("<<<END>>>")
    raise SystemExit(0)
lines = ["== 段落 =="]
for p in doc.paragraphs:
    if p.text.strip():
        lines.append(f"[{{p.style.name}}] {{p.text}}")
for ti, table in enumerate(doc.tables, 1):
    lines.append(f"== 表格 {{ti}} ==")
    for row in table.rows:
        lines.append(" | ".join(c.text for c in row.cells))
print("<<<JSON>>>")
print(json.dumps({"text": "\\n".join(lines)[:6000]}, ensure_ascii=False))
print("<<<END>>>")`
  }
}

export const W15_SCHEMAS: InteractiveToolSchema[] = [vaultAddSchema, vaultListSchema, schedOnceSchema, wordReadSchema]
