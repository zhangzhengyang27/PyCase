// tool-schemas-w4.ts：W4 七个轻量交互工具（JWT 解码 / .env 校验 / Markdown TOC /
// gitignore 生成 / 文本规范化 / 批量查找替换 / 密码生成）。
// 只依赖 interactive-tools 的类型（type-only，运行时零导入）；口径以 tool-golden.json
// 为双端唯一事实（Python 参考实现：tests/test_tool_golden.py）。
import type { InteractiveToolSchema } from './interactive-tools'

const INVALID_CODE = '# 补全输入后自动生成代码'
const str = (v: unknown): string => String(v ?? '')

// ---------------------------------------------------------------------------
// 1. JWT 解码器（不验签——签名校验属安全功能，声明式排除）
// ---------------------------------------------------------------------------
function b64uDecode(s: string): string {
  const b64 = s.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (s.length % 4)) % 4)
  // atob 出的是 Latin-1 字节串，逐字节转 UTF-8（中文 payload 正确解码）
  return decodeURIComponent([...atob(b64)].map((c) => `%${c.charCodeAt(0).toString(16).padStart(2, '0')}`).join(''))
}

const fmtUtc = (epochSec: number): string =>
  `${new Date(epochSec * 1000).toISOString().slice(0, 19).replace('T', ' ')} UTC`

export const jwtSchema: InteractiveToolSchema = {
  id: 'interactive:jwt',
  title: 'JWT 解码器',
  description: '解出 header/payload 与标准声明（exp/iat 按 UTC）；不校验签名——本工具只做解码，验签请用服务端。',
  tags: ['安全'],
  fields: [{ key: 'token', label: 'JWT', type: 'textarea', required: true, placeholder: 'eyJhbGciOi…' }],
  compute: (v) => {
    const token = str(v.token).trim()
    if (!token) return { error: '请输入 JWT' }
    const parts = token.split('.')
    if (parts.length !== 3) return { error: 'JWT 需为三段式（header.payload.signature）' }
    try {
      const header = JSON.parse(b64uDecode(parts[0]!)) as Record<string, unknown>
      const payload = JSON.parse(b64uDecode(parts[1]!)) as Record<string, unknown>
      const rows = [
        { label: 'alg', value: str(header.alg || '—') },
        ...(payload.exp !== undefined ? [{ label: 'exp（UTC）', value: fmtUtc(Number(payload.exp)) }] : []),
        ...(payload.iat !== undefined ? [{ label: 'iat（UTC）', value: fmtUtc(Number(payload.iat)) }] : []),
        { label: '签名长度', value: `${parts[2]!.length} 字符（未校验）` }
      ]
      return {
        rows,
        text: `${JSON.stringify(header, null, 2)}\n\n${JSON.stringify(payload, null, 2)}`
      }
    } catch (e) {
      return { error: `解码失败：${(e as Error).message}` }
    }
  },
  pyCode: (v) => {
    const token = str(v.token).trim()
    if (!token || token.split('.').length !== 3) return INVALID_CODE
    return `"""JWT 解码（不验签）。"""
import base64, json

h, p, sig = "${token}".split(".")
pad = lambda s: s + "=" * (-len(s) % 4)
header = json.loads(base64.urlsafe_b64decode(pad(h)))
payload = json.loads(base64.urlsafe_b64decode(pad(p)))
from datetime import datetime, timezone
print(json.dumps(header, ensure_ascii=False, indent=2))
print(json.dumps(payload, ensure_ascii=False, indent=2))
if "exp" in payload:
    print("exp:", datetime.fromtimestamp(payload["exp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "UTC")
print("签名长度:", len(sig), "字符（未校验）")
`
  }
}

// ---------------------------------------------------------------------------
// 2. .env 校验器（对比 .env 与 .env.example 的缺失/多余/空值键）
// ---------------------------------------------------------------------------
function parseEnv(text: string): { keys: string[]; empty: string[] } {
  const keys: string[] = []
  const empty: string[] = []
  for (const ln of text.split('\n')) {
    const s = ln.trim()
    if (!s || s.startsWith('#') || !s.includes('=')) continue
    const k = s.slice(0, s.indexOf('=')).trim()
    if (!k) continue
    keys.push(k)
    if (!s.slice(s.indexOf('=') + 1).trim()) empty.push(k)
  }
  return { keys, empty }
}

export const envCheckSchema: InteractiveToolSchema = {
  id: 'interactive:env-check',
  title: '.env 校验器',
  description: '对比 .env 与 .env.example：缺失键、多余键、空值键一目了然。跳过 # 注释与空行。',
  tags: ['配置'],
  fields: [
    { key: 'env', label: '.env 内容', type: 'textarea', required: true, placeholder: 'HOST=localhost\nPORT=5432' },
    { key: 'example', label: '.env.example 内容', type: 'textarea', required: true, placeholder: 'HOST=\nPORT=' }
  ],
  compute: (v) => {
    const envText = str(v.env)
    const exText = str(v.example)
    if (!envText.trim() && !exText.trim()) return { error: '请至少输入一份配置' }
    const env = parseEnv(envText)
    const ex = parseEnv(exText)
    const missing = ex.keys.filter((k) => !env.keys.includes(k))
    const extra = env.keys.filter((k) => !ex.keys.includes(k))
    return {
      rows: [
        { label: '缺失于 .env', value: missing.join(', ') || '无' },
        { label: '多余于 .env', value: extra.join(', ') || '无' },
        { label: '.env 空值键', value: env.empty.join(', ') || '无' }
      ]
    }
  },
  pyCode: (v) => {
    const envText = str(v.env)
    const exText = str(v.example)
    if (!envText.trim() && !exText.trim()) return INVALID_CODE
    return `""".env 差异（跳过 # 注释与空行）。"""
def parse_env(t):
    keys, empty = [], []
    for ln in t.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, val = s.partition("=")
        k = k.strip()
        if not k:
            continue
        keys.append(k)
        if not val.strip():
            empty.append(k)
    return keys, empty

env_keys, env_empty = parse_env(${JSON.stringify(envText)})
ex_keys, _ = parse_env(${JSON.stringify(exText)})
print("缺失于 .env:", ", ".join(k for k in ex_keys if k not in env_keys) or "无")
print("多余于 .env:", ", ".join(k for k in env_keys if k not in ex_keys) or "无")
print(".env 空值键:", ", ".join(env_empty) or "无")
`
  }
}

// ---------------------------------------------------------------------------
// 3. Markdown 目录生成（GitHub 锚点口径；跳过代码围栏；重名 -1 去重）
// ---------------------------------------------------------------------------
function ghAnchor(title: string): string {
  const lowered = title.trim().toLowerCase()
  const kept = [...lowered].filter((ch) => /[\p{L}\p{N}_ -]/u.test(ch)).join('')
  return kept.replace(/ /g, '-')
}

export function buildToc(text: string, lo: number, hi: number): { items: string[] } {
  const items: string[] = []
  let fence = false
  const counts: Record<string, number> = {}
  for (const ln of text.split('\n')) {
    if (ln.trim().startsWith('```')) {
      fence = !fence
      continue
    }
    if (fence) continue
    const m = /^(#{1,6})\s+(.+?)\s*$/.exec(ln)
    if (!m) continue
    const lvl = m[1]!.length
    const title = m[2]!.trim()
    if (lvl < lo || lvl > hi) continue
    let a = ghAnchor(title)
    const n = counts[a] ?? 0
    counts[a] = n + 1
    if (n) a = `${a}-${n}`
    items.push(`${'  '.repeat(lvl - lo)}- [${title}](#${a})`)
  }
  return { items }
}

export const mdTocSchema: InteractiveToolSchema = {
  id: 'interactive:md-toc',
  title: 'Markdown 目录生成',
  description: '提取 ATX 标题生成 TOC：GitHub 风格锚点、重名自动 -1 去重、代码围栏内的 # 不算标题。',
  tags: ['Markdown'],
  fields: [
    { key: 'text', label: 'Markdown', type: 'textarea', required: true, placeholder: '# 标题\n## 小节…' },
    {
      key: 'minLevel',
      label: '起始层级',
      type: 'select',
      default: '2',
      width: 'half',
      options: [1, 2, 3].map((n) => ({ value: String(n), label: `h${n}` }))
    },
    {
      key: 'maxLevel',
      label: '截止层级',
      type: 'select',
      default: '6',
      width: 'half',
      options: [3, 4, 5, 6].map((n) => ({ value: String(n), label: `h${n}` }))
    }
  ],
  compute: (v) => {
    const text = str(v.text)
    if (!text.trim()) return { error: '请输入 Markdown' }
    const lo = Number(v.minLevel ?? 2)
    const hi = Number(v.maxLevel ?? 6)
    if (lo > hi) return { error: '起始层级不能大于截止层级' }
    const { items } = buildToc(text, lo, hi)
    return { primary: { value: String(items.length), unit: '条' }, text: items.join('\n') || '（未发现标题）' }
  },
  pyCode: (v) => {
    const text = str(v.text)
    const lo = Number(v.minLevel ?? 2)
    const hi = Number(v.maxLevel ?? 6)
    if (!text.trim()) return INVALID_CODE
    return `"""Markdown TOC（GitHub 锚点口径 + 围栏跳过 + 重名去重）。"""
import re

def anchor(t):
    t = t.strip().lower()
    keep = [ch for ch in t if ch.isalnum() or ch in " -_"]
    return "".join(keep).replace(" ", "-")

items, fence, counts = [], False, {}
for ln in ${JSON.stringify(text)}.split("\\n"):
    if ln.strip().startswith("\`\`\`"):
        fence = not fence
        continue
    if fence:
        continue
    m = re.match(r"^(#{1,6})\\s+(.+?)\\s*$", ln)
    if not m:
        continue
    lvl, title = len(m.group(1)), m.group(2).strip()
    if lvl < ${lo} or lvl > ${hi}:
        continue
    a = anchor(title)
    n = counts.get(a, 0)
    counts[a] = n + 1
    if n:
        a = f"{a}-{n}"
    items.append("  " * (lvl - ${lo}) + f"- [{title}](#{a})")
print("\\n".join(items) or "（未发现标题）")
`
  }
}

// ---------------------------------------------------------------------------
// 4. gitignore 生成器（模板常量与黄金 expected 同源钉死）
// ---------------------------------------------------------------------------
const GITIGNORE_TEMPLATES: Record<string, string> = {
  Python: '__pycache__/\n*.py[cod]\n.venv/\n*.egg-info/\ndist/\nbuild/',
  Node: 'node_modules/\nnpm-debug.log*\n.npm/',
  Go: 'bin/\n',
  macOS: '.DS_Store\n',
  Windows: 'Thumbs.db\nDesktop.ini\n',
  VSCode: '.vscode/'
}
const GIT_ORDER = ['Python', 'Node', 'Go', 'macOS', 'Windows', 'VSCode']
const GIT_KEYS: Record<string, string> = {
  Python: 'py',
  Node: 'node',
  Go: 'go',
  macOS: 'mac',
  Windows: 'win',
  VSCode: 'vscode'
}

export const gitignoreSchema: InteractiveToolSchema = {
  id: 'interactive:gitignore',
  title: 'gitignore 生成器',
  description: '按技术栈拼装 .gitignore 模板（Python/Node/Go/macOS/Windows/VSCode）。',
  tags: ['生成器'],
  fields: GIT_ORDER.map((s) => ({
    key: GIT_KEYS[s]!,
    label: s,
    type: 'checkbox' as const,
    default: s === 'Python'
  })),
  compute: (v) => {
    const stacks = GIT_ORDER.filter((s) => v[GIT_KEYS[s]!] === true)
    if (!stacks.length) return { error: '至少选择一个技术栈' }
    return { text: stacks.map((s) => `# ${s}\n${GITIGNORE_TEMPLATES[s]}`).join('\n\n') + '\n' }
  },
  pyCode: (v) => {
    const stacks = GIT_ORDER.filter((s) => v[GIT_KEYS[s]!] === true)
    if (!stacks.length) return INVALID_CODE
    const content = stacks.map((s) => `# ${s}\n${GITIGNORE_TEMPLATES[s]}`).join('\n\n') + '\n'
    return `"""生成 .gitignore（${stacks.join(' + ')}）。"""
content = ${JSON.stringify(content)}
with open(".gitignore", "w", encoding="utf-8") as f:
    f.write(content)
print("已写入 .gitignore")
`
  }
}

// ---------------------------------------------------------------------------
// 5. 文本规范化（换行符统一 + 前导缩进转换；口径 = 变体生成代码延续）
// ---------------------------------------------------------------------------
export const normalizeSchema: InteractiveToolSchema = {
  id: 'interactive:normalize',
  title: '文本规范化',
  description: '换行符统一（LF/CRLF/CR）+ 前导缩进转换（Tab→2/4 空格；每 4 个前导空格→1 Tab，余数保留）。',
  tags: ['文本'],
  fields: [
    { key: 'text', label: '文本', type: 'textarea', required: true, placeholder: '粘贴要规范化的文本…' },
    {
      key: 'lineEnding',
      label: '目标行尾',
      type: 'select',
      default: 'LF',
      width: 'half',
      options: [
        { value: 'LF', label: 'LF（\\n）' },
        { value: 'CRLF', label: 'CRLF（\\r\\n）' },
        { value: 'CR', label: 'CR（\\r）' }
      ]
    },
    {
      key: 'indentMode',
      label: '缩进转换',
      type: 'select',
      default: 'none',
      width: 'half',
      options: [
        { value: 'none', label: '不转换' },
        { value: 'tab2', label: 'Tab → 2 空格' },
        { value: 'tab4', label: 'Tab → 4 空格' },
        { value: 'space4tab', label: '4 空格 → Tab' }
      ]
    }
  ],
  compute: (v) => {
    const text = str(v.text)
    if (!text.trim()) return { error: '请输入文本' }
    const lines = text.replace(/\r\n?/g, '\n').split('\n')
    const mode = str(v.indentMode ?? 'none')
    const out = lines.map((ln) => {
      if (mode === 'tab2' || mode === 'tab4') {
        const m = /^\t+/.exec(ln)
        if (m) return m[0].replace(/\t/g, mode === 'tab2' ? '  ' : '    ') + ln.slice(m[0].length)
      } else if (mode === 'space4tab') {
        const m = /^ +/.exec(ln)
        if (m) return '\t'.repeat(Math.floor(m[0].length / 4)) + ' '.repeat(m[0].length % 4) + ln.slice(m[0].length)
      }
      return ln
    })
    const eol = { LF: '\n', CRLF: '\r\n', CR: '\r' }[str(v.lineEnding ?? 'LF')] ?? '\n'
    return { primary: { value: String(out.length), unit: '行' }, text: out.join(eol) }
  },
  pyCode: (v) => {
    const text = str(v.text)
    const mode = str(v.indentMode ?? 'none')
    const ending = str(v.lineEnding ?? 'LF')
    if (!text.trim()) return INVALID_CODE
    return `"""文本规范化（换行符 + 前导缩进口径与页面一致）。"""
import re

lines = re.sub(r"\\r\\n?", "\\n", ${JSON.stringify(text)}).split("\\n")
out = []
for ln in lines:
    mode = ${JSON.stringify(mode)}
    if mode in ("tab2", "tab4"):
        m = re.match(r"^(\\t+)", ln)
        if m:
            w = "  " if mode == "tab2" else "    "
            ln = m.group(1).replace("\\t", w) + ln[len(m.group(1)):]
    elif mode == "space4tab":
        m = re.match(r"^( +)", ln)
        if m:
            n = len(m.group(1))
            ln = "\\t" * (n // 4) + " " * (n % 4) + ln[n:]
    out.append(ln)
eol = ${JSON.stringify(ending === 'LF' ? '\n' : ending === 'CRLF' ? '\r\n' : '\r')}
print(eol.join(out), end="")
`
  }
}

// ---------------------------------------------------------------------------
// 6. 批量查找替换（字面量 / 正则；$1 与 \\1 反向引用语法差异已在描述声明）
// ---------------------------------------------------------------------------
export const replaceSchema: InteractiveToolSchema = {
  id: 'interactive:find-replace',
  title: '批量查找替换',
  description:
    '字面量或正则替换（恒全量替换）：给出命中计数与结果。正则的反向引用用 JS 语法（$1），与 Python 的 \\1 不同。',
  tags: ['文本'],
  fields: [
    { key: 'text', label: '文本', type: 'textarea', required: true, placeholder: '原始文本…' },
    { key: 'find', label: '查找', type: 'text', required: true, width: 'half' },
    { key: 'replace', label: '替换为', type: 'text', default: '', width: 'half' },
    { key: 'regex', label: '正则', type: 'checkbox', help: '按正则表达式解释「查找」' },
    { key: 'ignoreCase', label: '忽略大小写', type: 'checkbox' }
  ],
  compute: (v) => {
    const text = str(v.text)
    const find = str(v.find)
    const repl = str(v.replace)
    if (!text.trim()) return { error: '请输入文本' }
    if (!find) return { error: '请输入查找内容' }
    if (v.regex === true) {
      let re: RegExp
      try {
        re = new RegExp(find, v.ignoreCase === true ? 'gi' : 'g')
      } catch (e) {
        return { error: `非法正则：${(e as Error).message}` }
      }
      const count = [...text.matchAll(re)].length
      return { primary: { value: String(count), unit: '处替换' }, text: text.replace(re, repl) }
    }
    if (v.ignoreCase === true) {
      const re = new RegExp(find.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
      const count = [...text.matchAll(re)].length
      return { primary: { value: String(count), unit: '处替换' }, text: text.replace(re, repl) }
    }
    const count = find ? text.split(find).length - 1 : 0
    return { primary: { value: String(count), unit: '处替换' }, text: text.split(find).join(repl) }
  },
  pyCode: (v) => {
    const text = str(v.text)
    const find = str(v.find)
    const repl = str(v.replace)
    if (!text.trim() || !find) return INVALID_CODE
    if (v.regex === true) {
      return `"""正则批量替换（Python \\1 反向引用语法，与 JS $1 不同）。"""
import re

text = ${JSON.stringify(text)}
new, n = re.subn(r'''${find}''', ${JSON.stringify(repl)}, text, flags=re.I if ${v.ignoreCase === true ? 'True' : 'False'} else 0)
print(f"共 {n} 处")
print(new)
`
    }
    return `"""字面量批量替换（忽略大小写走 re.escape + re.I）。"""
text = ${JSON.stringify(text)}
find = ${JSON.stringify(find)}
repl = ${JSON.stringify(repl)}
ignore = ${v.ignoreCase === true ? 'True' : 'False'}
if ignore:
    import re
    new, n = re.subn(re.escape(find), repl.replace("\\\\", "\\\\\\\\"), text, flags=re.I)
else:
    n = text.count(find)
    new = text.replace(find, repl)
print(f"共 {n} 处")
print(new)
`
  }
}

// ---------------------------------------------------------------------------
// 7. 密码生成器（随机型：黄金钉字符集常量与「每类至少一个」规则）
// ---------------------------------------------------------------------------
const PW_POOLS: Record<string, string> = {
  lower: 'abcdefghijklmnopqrstuvwxyz',
  upper: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  digits: '0123456789',
  symbols: '!@#$%^&*-_=+?'
}
const PW_AMBIGUOUS = '0Oo1lI'

function shuffled(arr: string[]): string[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const b = randomBytesBelow(i + 1)
    ;[a[i], a[b]] = [a[b]!, a[i]!]
  }
  return a
}
function randomBytesBelow(n: number): number {
  // 拒绝采样消偏差：256 % n 的余数段重抽
  const lim = 256 - (256 % n)
  for (;;) {
    const b = new Uint8Array(1)
    globalThis.crypto.getRandomValues(b)
    if (b[0]! < lim) return b[0]! % n
  }
}

export const pwdGenSchema: InteractiveToolSchema = {
  id: 'interactive:pwd-gen',
  title: '密码生成器',
  description: '按字符集生成强密码：保证每个所选字符集至少出现一个；可排除易混淆字符（0Oo1lI）。',
  tags: ['安全', '生成器'],
  fields: [
    { key: 'length', label: '长度', type: 'number', default: 16, width: 'half', help: '8~64' },
    { key: 'lower', label: '小写', type: 'checkbox', default: true },
    { key: 'upper', label: '大写', type: 'checkbox', default: true },
    { key: 'digits', label: '数字', type: 'checkbox', default: true },
    { key: 'symbols', label: '符号', type: 'checkbox', default: true },
    { key: 'noAmbiguous', label: '排除易混淆', type: 'checkbox', default: true, help: '剔除 0Oo1lI' }
  ],
  compute: (v) => {
    const len = Math.trunc(Number(v.length ?? 16))
    if (!Number.isFinite(len) || len < 8 || len > 64) return { error: '长度需为 8~64 的整数' }
    const selected = Object.entries(PW_POOLS)
      .filter(([k]) => v[k] === true)
      .map(([k, pool]) => ({
        k,
        pool: v.noAmbiguous === true ? [...pool].filter((c) => !PW_AMBIGUOUS.includes(c)).join('') : pool
      }))
      .filter(({ pool }) => pool.length)
    if (!selected.length) return { error: '至少选择一个字符集' }
    const all = selected.map(({ pool }) => pool).join('')
    const picked = selected.map(({ pool }) => pool[randomBytesBelow(pool.length)]!)
    while (picked.length < len) picked.push(all[randomBytesBelow(all.length)]!)
    return { primary: { value: shuffled(picked).slice(0, len).join('') } }
  },
  pyCode: (v) => {
    const len = Math.trunc(Number(v.length ?? 16))
    if (!Number.isFinite(len) || len < 8 || len > 64) return INVALID_CODE
    const selected = Object.entries(PW_POOLS).filter(([k]) => v[k] === true)
    if (!selected.length) return INVALID_CODE
    return `"""密码生成（每类至少一个 + Fisher-Yates 洗牌）。"""
import secrets, string

POOLS = ${JSON.stringify(Object.fromEntries(selected.map(([k]) => [k, PW_POOLS[k]])))}
AMBIG = ${JSON.stringify(PW_AMBIGUOUS)}
no_amb = ${v.noAmbiguous === true ? 'True' : 'False'}
pools = {k: ''.join(c for c in p if c not in AMBIG) if no_amb else p for k, p in POOLS.items()}
all_chars = ''.join(pools.values())
picked = [secrets.choice(p) for p in pools.values()]
while len(picked) < ${len}:
    picked.append(secrets.choice(all_chars))
# Fisher-Yates
for i in range(len(picked) - 1, 0, -1):
    j = secrets.randbelow(i + 1)
    picked[i], picked[j] = picked[j], picked[i]
print(''.join(picked[:${len}]))
`
  }
}

export const W4_SCHEMAS: InteractiveToolSchema[] = [
  jwtSchema,
  envCheckSchema,
  mdTocSchema,
  gitignoreSchema,
  normalizeSchema,
  replaceSchema,
  pwdGenSchema
]
