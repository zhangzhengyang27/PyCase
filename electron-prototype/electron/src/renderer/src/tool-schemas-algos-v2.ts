// tool-schemas-algos-v2.ts：算法可视化补齐 ×6——矩阵乘法/最长公共子序列/并查集/GCD-LCM/矩阵旋转/词频交互页。
// 全部纯前端即时计算（date-core 模式），吸收 bulk_basics 算法变体的参数空间。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')

function matParse(text: string): number[][] | null {
  const rows = text
    .split('\n')
    .filter((l) => l.trim())
    .map((row) => row.split(/[,;]/).map((c) => Number(c.trim())))
  if (!rows.length || rows.some((r) => !r.length || !r.every(Number.isFinite))) return null
  return rows as number[][]
}

export const matmulSchema: InteractiveToolSchema = {
  id: 'interactive:matrix-multiply',
  title: '矩阵乘法',
  description: 'A×B 矩阵乘法（A 列数必须等于 B 行数），结果表格化展示。',
  tags: ['算法'],
  fields: [
    { key: 'a', label: '矩阵 A（每行一行，逗号分隔）', type: 'textarea', required: true, placeholder: '1,2\n3,4' },
    { key: 'b', label: '矩阵 B', type: 'textarea', required: true, placeholder: '5,6\n7,8' }
  ],
  compute: (v) => {
    const a = matParse(str(v.a))
    const b = matParse(str(v.b))
    if (!a || !b) return { error: '请输入两个有效矩阵' }
    if (a[0]!.length !== b.length) return { error: `A 的列数 (${a[0]!.length}) 必须等于 B 的行数 (${b.length})` }
    const result = a.map((row) => b[0]!.map((_, j) => row.reduce((sum, x, k) => sum + x * b[k]![j]!, 0)))
    return {
      rows: [{ label: '结果规模', value: `${result.length}×${result[0]!.length}` }],
      table: { columns: b[0]!.map((_, j) => `列${j + 1}`), rows: result.map((r) => r.map(String)) }
    }
  },
  pyCode: (v) => {
    const a = matParse(str(v.a))
    const b = matParse(str(v.b))
    if (!a || !b) return '# 输入有效矩阵后自动生成代码'
    return `"""矩阵乘法（纯 Python 三重循环）。"""
A = ${JSON.stringify(a)}
B = ${JSON.stringify(b)}
C = [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]
for row in C:
    print(row)
`
  }
}

export const lcsSchema: InteractiveToolSchema = {
  id: 'interactive:lcs',
  title: '最长公共子序列',
  description: '动态规划求两段文本的 LCS（长度 + 序列本身）。',
  tags: ['算法'],
  fields: [
    { key: 'a', label: '文本 A', type: 'text', required: true, default: 'ABCBDAB', width: 'half' },
    { key: 'b', label: '文本 B', type: 'text', required: true, default: 'BDCABA', width: 'half' }
  ],
  compute: (v) => {
    const a = str(v.a)
    const b = str(v.b)
    if (!a || !b) return { error: '请输入两段文本' }
    if (a.length > 200 || b.length > 200) return { error: '文本过长（各 ≤200 字符）' }
    const m = a.length,
      n = b.length
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))
    for (let i = 1; i <= m; i++)
      for (let j = 1; j <= n; j++)
        dp[i]![j] = a[i - 1] === b[j - 1] ? dp[i - 1]![j - 1]! + 1 : Math.max(dp[i - 1]![j]!, dp[i]![j - 1]!)
    let i = m,
      j = n
    const seq: string[] = []
    while (i > 0 && j > 0) {
      if (a[i - 1] === b[j - 1]) {
        seq.unshift(a[i - 1]!)
        i--
        j--
      } else if (dp[i - 1]![j]! >= dp[i]![j - 1]!) i--
      else j--
    }
    return {
      primary: { value: String(dp[m]![n]), unit: 'LCS 长度' },
      rows: [{ label: '序列', value: seq.join(' ') || '（无）' }]
    }
  },
  pyCode: (v) => {
    const a = str(v.a)
    const b = str(v.b)
    if (!a || !b) return '# 输入两段文本后自动生成代码'
    return `"""最长公共子序列（DP）。"""
a, b = ${JSON.stringify(a)}, ${JSON.stringify(b)}
m, n = len(a), len(b)
dp = [[0] * (n + 1) for _ in range(m + 1)]
for i in range(1, m + 1):
    for j in range(1, n + 1):
        dp[i][j] = dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] else max(dp[i - 1][j], dp[i][j - 1])
i, j, seq = m, n, []
while i > 0 and j > 0:
    if a[i - 1] == b[j - 1]:
        seq.append(a[i - 1])
        i -= 1; j -= 1
    elif dp[i - 1][j] >= dp[i][j - 1]:
        i -= 1
    else:
        j -= 1
print(f"LCS 长度: {{dp[m][n]}}")
print("".join(reversed(seq)))
`
  }
}

export const unionFindSchema: InteractiveToolSchema = {
  id: 'interactive:union-find',
  title: '并查集连通分量',
  description: '边列表「u,v」→ 连通分量个数与分组。',
  tags: ['算法'],
  fields: [
    { key: 'n', label: '节点数', type: 'number', default: 6, width: 'half', help: '节点编号 0 ~ n-1' },
    { key: 'edges', label: '边（CSV：u,v）', type: 'textarea', required: true, placeholder: '0,1\n1,2\n3,4' }
  ],
  compute: (v) => {
    const n = Math.trunc(Number(v.n ?? 6))
    if (!Number.isFinite(n) || n < 1 || n > 1000) return { error: '节点数需为 1~1000' }
    const parent = Array.from({ length: n }, (_, i) => i)
    function find(x: number): number {
      while (parent[x] !== x) {
        parent[x] = parent[parent[x]]!
        x = parent[x]!
      }
      return x
    }
    for (const ln of str(v.edges).split('\n')) {
      const parts = ln.split(',').map((s) => Number(s.trim()))
      if (parts.length === 2 && parts.every(Number.isFinite) && parts[0]! < n && parts[1]! < n) {
        const ra = find(parts[0]!),
          rb = find(parts[1]!)
        if (ra !== rb) parent[rb] = ra
      }
    }
    const groups = new Map<number, number[]>()
    for (let i = 0; i < n; i++) {
      const r = find(i)
      if (!groups.has(r)) groups.set(r, [])
      groups.get(r)!.push(i)
    }
    return {
      primary: { value: String(groups.size), unit: '个连通分量' },
      list: [...groups.values()].map((g) => `{${g.join(',')}}`)
    }
  },
  pyCode: (v) => {
    const n = Math.trunc(Number(v.n ?? 6))
    const edges = str(v.edges)
    if (!Number.isFinite(n) || n < 1) return '# 补全节点数后自动生成代码'
    return `"""并查集连通分量。"""
parent = list(range(${n}))
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

for ln in ${JSON.stringify(edges)}.splitlines():
    parts = ln.strip().split(",")
    if len(parts) == 2:
        u, v = int(parts[0]), int(parts[1])
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[rv] = ru

groups: dict = {}
for i in range(${n}):
    groups.setdefault(find(i), []).append(i)
print(f"连通分量数: {{len(groups)}}")
for g in groups.values():
    print(g)
`
  }
}

export const gcdLcmSchema: InteractiveToolSchema = {
  id: 'interactive:gcd-lcm',
  title: 'GCD/LCM',
  description: '两个整数的最大公约数（欧几里得）与最小公倍数。',
  tags: ['算法'],
  fields: [
    { key: 'a', label: '整数 A', type: 'number', default: 48, width: 'half' },
    { key: 'b', label: '整数 B', type: 'number', default: 36, width: 'half' }
  ],
  compute: (v) => {
    let a = Math.abs(Math.trunc(Number(v.a ?? 0)))
    let b = Math.abs(Math.trunc(Number(v.b ?? 0)))
    if (!a || !b) return { error: '请输入两个非零整数' }
    const origA = a,
      origB = b
    while (b) {
      ;[a, b] = [b, a % b]
    }
    return {
      primary: { value: String(a), unit: 'GCD' },
      rows: [{ label: 'LCM', value: String((origA / a) * origB) }]
    }
  },
  pyCode: (v) => {
    const a = Math.abs(Math.trunc(Number(v.a ?? 0)))
    const b = Math.abs(Math.trunc(Number(v.b ?? 0)))
    if (!a || !b) return '# 输入两个非零整数后自动生成代码'
    return `"""GCD（欧几里得）与 LCM。"""
a, b = ${a}, ${b}
x, y = a, b
while y:
    x, y = y, x % y
print(f"GCD = {{x}}")
print(f"LCM = {{a * b // x}}")
`
  }
}

export const matRotateSchema: InteractiveToolSchema = {
  id: 'interactive:matrix-rotate',
  title: '矩阵旋转',
  description: '方阵顺时针/逆时针旋转 90°。',
  tags: ['算法'],
  fields: [
    { key: 'mat', label: '方阵（每行一行）', type: 'textarea', required: true, placeholder: '1,2,3\n4,5,6\n7,8,9' },
    {
      key: 'dir',
      label: '方向',
      type: 'select',
      default: 'cw',
      width: 'half',
      options: [
        { value: 'cw', label: '顺时针 90°' },
        { value: 'ccw', label: '逆时针 90°' }
      ]
    }
  ],
  compute: (v) => {
    const rows = str(v.mat)
      .split('\n')
      .filter((l) => l.trim())
      .map((r) => r.split(',').map((c) => c.trim()))
    if (rows.length < 2) return { error: '请输入至少 2×2 的矩阵' }
    const n = rows.length
    if (rows.some((r) => r.length !== n)) return { error: '需要方阵（行列数相同）' }
    const out =
      str(v.dir ?? 'cw') === 'cw'
        ? rows[0]!.map((_, j) => rows.map((r) => r[j]!).reverse())
        : rows[0]!.map((_, j) => rows.map((r) => r[n - 1 - j]!))
    return { text: out.map((r) => r.join('  ')).join('\n') }
  },
  pyCode: (v) => {
    const rows = str(v.mat)
      .split('\n')
      .filter((l) => l.trim())
    const cw = str(v.dir ?? 'cw') === 'cw'
    if (rows.length < 2) return '# 输入矩阵后自动生成代码'
    return `"""矩阵旋转（${cw ? '顺时针' : '逆时针'} 90°）。"""
mat = [
${rows
  .map(
    (r) =>
      '    [' +
      r
        .split(',')
        .map((c) => JSON.stringify(c.trim()))
        .join(', ') +
      '],'
  )
  .join('\n')}
]
if ${cw ? 'True' : 'False'}:
    result = [list(row) for row in zip(*mat[::-1])]
else:
    result = [list(row) for row in zip(*mat)][::-1]
for row in result:
    print(row)
`
  }
}

export const wordFreqSchema: InteractiveToolSchema = {
  id: 'interactive:word-freq',
  title: '词频统计',
  description: '文本 → 词频 Top N（按空格分词，标点剥离，大小写归一）。',
  tags: ['文本', '统计'],
  fields: [
    {
      key: 'text',
      label: '文本',
      type: 'textarea',
      required: true,
      placeholder: 'python is simple python is powerful'
    },
    { key: 'topn', label: 'Top N', type: 'number', default: 10, width: 'half' }
  ],
  compute: (v) => {
    const text = str(v.text)
    if (!text.trim()) return { error: '请输入文本' }
    const topn = Math.max(1, Math.min(100, Math.trunc(Number(v.topn ?? 10)) || 10))
    const freq = new Map<string, number>()
    for (const w of text
      .toLowerCase()
      .replace(/[.,!?;:()"]/g, '')
      .split(/\s+/)) {
      if (!w) continue
      freq.set(w, (freq.get(w) ?? 0) + 1)
    }
    const sorted = [...freq.entries()].sort((a, b) => b[1] - a[1]).slice(0, topn)
    return {
      primary: { value: String(freq.size), unit: '去重词数' },
      table: { columns: ['词', '频次'], rows: sorted.map(([w, c]) => [w, String(c)]) }
    }
  },
  pyCode: (v) => {
    const text = str(v.text)
    const topn = Math.max(1, Math.min(100, Math.trunc(Number(v.topn ?? 10)) || 10))
    if (!text.trim()) return '# 输入文本后自动生成代码'
    return `"""词频统计：Top ${topn}。"""
from collections import Counter

text = ${JSON.stringify(text)}
words = [w.strip(".,!?;:()").lower() for w in text.split()]
words = [w for w in words if w]
counter = Counter(words)
for word, cnt in counter.most_common(${topn}):
    print(f"{{word:>12}}  {{cnt}}")
print("去重词数:", len(counter))
`
  }
}

export const ALGO2_SCHEMAS: InteractiveToolSchema[] = [
  matmulSchema,
  lcsSchema,
  unionFindSchema,
  gcdLcmSchema,
  matRotateSchema,
  wordFreqSchema
]
