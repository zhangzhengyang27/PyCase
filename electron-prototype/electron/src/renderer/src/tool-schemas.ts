// tool-schemas.ts：W1 三个 schema 驱动交互工具（温度换算 / 进制转换 / 凯撒密码）。
// 只依赖 interactive-tools 的类型（type-only，运行时零导入——避免与注册表成环）；
// compute 与 pyCode 都是纯函数，口径以 tool-golden.json 为双端唯一事实
// （Python 参考实现：tests/test_tool_golden.py）。
import type { InteractiveToolSchema } from './interactive-tools'

const INVALID_CODE = '# 补全输入后自动生成代码'

// ---------------------------------------------------------------------------
// 温度换算器（吸收 bulk_basics 温度换算器 ×3 变体）
// ---------------------------------------------------------------------------
export const tempConvertSchema: InteractiveToolSchema = {
  id: 'interactive:temp-convert',
  title: '温度换算器',
  description: '摄氏/华氏/开尔文互转：任选源单位，三单位对照即时刷新； Kelvin 锚点口径，低于绝对零度给引导。',
  tags: ['换算'],
  fields: [
    { key: 'value', label: '温度值', type: 'number', required: true, placeholder: '36.6', width: 'half' },
    {
      key: 'from',
      label: '源单位',
      type: 'select',
      default: 'C',
      width: 'half',
      options: [
        { value: 'C', label: '摄氏 ℃' },
        { value: 'F', label: '华氏 ℉' },
        { value: 'K', label: '开尔文 K' }
      ]
    },
    {
      key: 'to',
      label: '目标单位',
      type: 'select',
      default: 'F',
      width: 'half',
      options: [
        { value: 'C', label: '摄氏 ℃' },
        { value: 'F', label: '华氏 ℉' },
        { value: 'K', label: '开尔文 K' }
      ]
    },
    {
      key: 'precision',
      label: '小数位',
      type: 'select',
      default: '1',
      width: 'half',
      options: [
        { value: '0', label: '整数' },
        { value: '1', label: '1 位' },
        { value: '2', label: '2 位' }
      ]
    }
  ],
  compute: (v) => {
    const raw = Number(v.value)
    if (v.value === undefined || v.value === '' || !Number.isFinite(raw)) return { error: '请输入温度数值' }
    const from = String(v.from ?? 'C')
    const to = String(v.to ?? 'F')
    // Kelvin 锚点：任意单位先统一到 K，再反解到目标单位（与 Python 参考实现同构）
    const k = from === 'C' ? raw + 273.15 : from === 'F' ? ((raw - 32) * 5) / 9 + 273.15 : raw
    if (k < 0) return { error: '低于绝对零度（K < 0）' }
    const p = Math.min(Math.max(0, Number(v.precision ?? 1) || 0), 6)
    const c = k - 273.15
    const f = (c * 9) / 5 + 32
    const map: Record<string, number> = { C: c, F: f, K: k }
    const fmt = (x: number): string => x.toFixed(p)
    return {
      primary: { value: fmt(map[to]), unit: to === 'C' ? '℃' : to === 'F' ? '℉' : 'K' },
      rows: [
        { label: '摄氏 ℃', value: fmt(map.C), copy: true },
        { label: '华氏 ℉', value: fmt(map.F), copy: true },
        { label: '开尔文 K', value: fmt(map.K), copy: true }
      ]
    }
  },
  pyCode: (v) => {
    const raw = Number(v.value)
    if (v.value === undefined || v.value === '' || !Number.isFinite(raw)) return INVALID_CODE
    const from = String(v.from ?? 'C')
    const p = Math.min(Math.max(0, Number(v.precision ?? 1) || 0), 6)
    return `"""温度换算：${raw}${from} → 三单位对照（Kelvin 锚点口径）。"""
v = float("${raw}")
k = v + 273.15 if "${from}" == "C" else (v - 32) * 5 / 9 + 273.15 if "${from}" == "F" else v
c = k - 273.15
f = c * 9 / 5 + 32
print(f"摄氏: {c:.${p}f} ℃")
print(f"华氏: {f:.${p}f} ℉")
print(f"开尔文: {k:.${p}f} K")
`
  }
}

// ---------------------------------------------------------------------------
// 进制转换器（吸收 bulk_basics 进制转换器 ×5 变体；字符串入 + BigInt 防大数精度丢失）
// ---------------------------------------------------------------------------
const BASE_DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'

function toAnyBase(n: bigint, base: number, neg: boolean): string {
  let x = n
  let out = ''
  while (x) {
    out = BASE_DIGITS[Number(x % BigInt(base))]! + out
    x /= BigInt(base)
  }
  return (neg ? '-' : '') + (out || '0')
}

export const baseConvertSchema: InteractiveToolSchema = {
  id: 'interactive:base-convert',
  title: '进制转换器',
  description: '2~36 进制互转：字符串入（大数不丢精度），base 2/8/10/16 一览；非法字符即时指出。',
  tags: ['数学'],
  fields: [
    { key: 'value', label: '数值', type: 'text', required: true, placeholder: '255 或 ff', width: 'half' },
    {
      key: 'fromBase',
      label: '源进制',
      type: 'select',
      default: '10',
      width: 'half',
      options: [2, 8, 10, 16, 36].map((b) => ({ value: String(b), label: `base ${b}` }))
    }
  ],
  compute: (v) => {
    const s = String(v.value ?? '').trim()
    if (!s) return { error: '请输入数值' }
    const b = Number(v.fromBase ?? 10)
    const m = /^(-?)([0-9a-z]+)$/i.exec(s)
    if (!m) return { error: '只支持数字与字母（可带负号）' }
    const neg = m[1] === '-'
    let n = 0n
    for (const ch of m[2]!.toLowerCase()) {
      const d = BASE_DIGITS.indexOf(ch)
      if (d < 0 || d >= b) return { error: `「${ch}」不是 ${b} 进制的合法字符` }
      n = n * BigInt(b) + BigInt(d)
    }
    return {
      rows: [2, 8, 10, 16].map((bb) => ({ label: `base ${bb}`, value: toAnyBase(n, bb, neg), copy: true }))
    }
  },
  pyCode: (v) => {
    const s = String(v.value ?? '').trim()
    const b = Number(v.fromBase ?? 10)
    if (!s || !/^[0-9a-z]+$/i.test(s) || !Number.isInteger(b)) return INVALID_CODE
    return `"""进制转换：${s}(base ${b}) → 各进制对照（int(s, base) 解析）。"""
digits = "0123456789abcdefghijklmnopqrstuvwxyz"
n = abs(int("${s}", ${b}))
neg = "${s}".startswith("-")
for base in (2, 8, 10, 16):
    x, out = n, ""
    while x:
        out = digits[x % base] + out
        x //= base
    prefix = "-" if neg else ""
    print(f"base-{base:>2}: {prefix}{out or '0'}")
`
  }
}

// ---------------------------------------------------------------------------
// 凯撒密码（吸收 bulk_basics 凯撒密码 ×4 变体）
// ---------------------------------------------------------------------------
function shiftText(text: string, k: number): string {
  const sh = (ch: string): string => {
    if (ch >= 'a' && ch <= 'z') return String.fromCharCode(((((ch.charCodeAt(0) - 97 + k) % 26) + 26) % 26) + 97)
    if (ch >= 'A' && ch <= 'Z') return String.fromCharCode(((((ch.charCodeAt(0) - 65 + k) % 26) + 26) % 26) + 65)
    return ch
  }
  return [...text].map(sh).join('')
}

export const caesarCipherSchema: InteractiveToolSchema = {
  id: 'interactive:caesar-cipher',
  title: '凯撒密码',
  description: '移位加密与解密（mod 26 归一，保留大小写、非字母跳过）；附自解密回验。',
  tags: ['密码学'],
  fields: [
    { key: 'text', label: '文本', type: 'textarea', required: true, placeholder: 'Hello, World!' },
    { key: 'shift', label: '移位数', type: 'number', default: 3, width: 'half', help: '可为负；按 mod 26 归一' },
    {
      key: 'mode',
      label: '模式',
      type: 'select',
      default: 'encrypt',
      width: 'half',
      options: [
        { value: 'encrypt', label: '加密' },
        { value: 'decrypt', label: '解密' }
      ]
    }
  ],
  compute: (v) => {
    const text = String(v.text ?? '')
    if (!text) return { error: '请输入文本' }
    const raw = Number.isFinite(Number(v.shift)) ? Math.trunc(Number(v.shift)) : 3
    // 模 26 归一（负数移位取同余正代表：-1 ≡ 25；JS % 对负数返回负值，需双取模）
    const norm = ((raw % 26) + 26) % 26
    const k = v.mode === 'decrypt' ? -norm : norm
    const out = shiftText(text, k)
    return {
      primary: { value: out },
      rows: [
        { label: '有效移位', value: `${norm}（mod 26）` },
        { label: v.mode === 'decrypt' ? '加密回验' : '解密回验', value: shiftText(out, -k), copy: true }
      ]
    }
  },
  pyCode: (v) => {
    const text = String(v.text ?? '')
    if (!text) return INVALID_CODE
    const raw = Number.isFinite(Number(v.shift)) ? Math.trunc(Number(v.shift)) : 3
    const norm = ((raw % 26) + 26) % 26
    const k = v.mode === 'decrypt' ? -norm : norm
    return `"""凯撒密码：移位 ${k}（${v.mode === 'decrypt' ? '解密' : '加密'}，mod 26 归一）。"""
def caesar(text, k):
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + k) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + k) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)

msg = ${JSON.stringify(text)}
result = caesar(msg, ${k})
print("原文:", msg)
print("结果:", result)
print("回验:", caesar(result, ${-k}))
`
  }
}

export const TOOL_SCHEMAS: InteractiveToolSchema[] = [tempConvertSchema, baseConvertSchema, caesarCipherSchema]

// ---------------------------------------------------------------------------
// 文本折行（吸收 bulk_basics 文本折行 ×5 变体；greedy 按词填充口径 = 变体代码同款）
// 口径：任意空白切词、单词内长度按 Unicode 码点计、超长词整词溢出不硬切、
//       词间以单空格连接。与 tests/test_tool_golden.py 的 ref_wrap 同构。
// ---------------------------------------------------------------------------
function greedyWrap(text: string, width: number): string[] {
  const lines: string[] = []
  let cur = ''
  for (const word of text.split(/\s+/).filter(Boolean)) {
    if ([...cur].length + [...word].length + 1 > width && cur) {
      lines.push(cur)
      cur = word
    } else {
      cur = (cur + ' ' + word).trim()
    }
  }
  if (cur) lines.push(cur)
  return lines
}

export const textWrapSchema: InteractiveToolSchema = {
  id: 'interactive:text-wrap',
  title: '文本折行',
  description: '按列宽 greedy 填充折行：任意空白切词、按 Unicode 码点计宽、超长词整词溢出不硬切。',
  tags: ['文本'],
  fields: [
    { key: 'text', label: '文本', type: 'textarea', required: true, placeholder: '粘贴要折行的文本…' },
    { key: 'width', label: '列宽', type: 'number', default: 28, width: 'half', help: '按字符数计（非显示宽度）' }
  ],
  compute: (v) => {
    const text = String(v.text ?? '')
    if (!text.trim()) return { error: '请输入文本' }
    const raw = Math.trunc(Number(v.width))
    if (!Number.isFinite(raw) || raw < 1) return { error: '列宽需为 ≥1 的整数' }
    const lines = greedyWrap(text, raw)
    return { primary: { value: String(lines.length), unit: '行' }, text: lines.join('\n') }
  },
  pyCode: (v) => {
    const text = String(v.text ?? '')
    const width = Math.trunc(Number(v.width))
    if (!text.trim() || !Number.isFinite(width) || width < 1) return INVALID_CODE
    return `"""文本折行：宽度 ${width} 列。"""
text = ${JSON.stringify(text)}
width = ${width}
lines, cur = [], ""
for word in text.split():
    if len(cur) + len(word) + 1 > width and cur:
        lines.append(cur)
        cur = word
    else:
        cur = (cur + " " + word).strip()
if cur:
    lines.append(cur)
for ln in lines:
    print(ln)
print(f"共 {len(lines)} 行")
`
  }
}

// ---------------------------------------------------------------------------
// 回文判定（吸收 bulk_basics 回文判定 ×3 变体；口径 = Python isalnum 归一 + 双指针）
// isalnum 的 Unicode 语义：汉字/全角数字都算「字母数字」，与 \p{L}\p{N} 对齐。
// ---------------------------------------------------------------------------
function normalizePalindrome(s: string): string[] {
  return [...s.toLowerCase()].filter((ch) => /[\p{L}\p{N}]/u.test(ch))
}

export const palindromeSchema: InteractiveToolSchema = {
  id: 'interactive:palindrome',
  title: '回文判定',
  description: '双指针回文检测：忽略大小写、标点与空白（Unicode 字母数字归一），给出归一化文本与首处差异。',
  tags: ['双指针'],
  fields: [{ key: 'text', label: '文本', type: 'textarea', required: true, placeholder: 'A man, a plan, a canal: Panama' }],
  compute: (v) => {
    const raw = String(v.text ?? '')
    if (!raw.trim()) return { error: '请输入文本' }
    const t = normalizePalindrome(raw)
    let i = 0
    let j = t.length - 1
    while (i < j) {
      if (t[i] !== t[j]) {
        return {
          primary: { value: '不是回文' },
          rows: [
            { label: '归一化后', value: t.join(''), copy: true },
            { label: '有效字符', value: String(t.length) },
            { label: '首处差异', value: `第 ${i} 位 '${t[i]}' ≠ '${t[j]}'` }
          ]
        }
      }
      i += 1
      j -= 1
    }
    return {
      primary: { value: '是回文' },
      rows: [
        { label: '归一化后', value: t.join('') || '（空）', copy: true },
        { label: '有效字符', value: String(t.length) }
      ]
    }
  },
  pyCode: (v) => {
    const raw = String(v.text ?? '')
    if (!raw.trim()) return INVALID_CODE
    return `"""回文判定（isalnum 归一 + 双指针）。"""
def is_palindrome(t):
    t = "".join(ch.lower() for ch in t if ch.isalnum())
    i, j = 0, len(t) - 1
    while i < j:
        if t[i] != t[j]:
            return False
        i += 1
        j -= 1
    return True

s = ${JSON.stringify(raw)}
norm = "".join(ch.lower() for ch in s if ch.isalnum())
print("归一化:", norm or "（空）")
print("判定:", "是回文" if is_palindrome(s) else "不是回文")
`
  }
}

// W2 追加注册：追加到 TOOL_SCHEMAS 尾部
TOOL_SCHEMAS.push(textWrapSchema, palindromeSchema)
