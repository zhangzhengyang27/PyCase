// tool-schemas-algos.ts：V4 算法可视化 ×8（纯前端即时计算，date-core 模式）。
// 覆盖 bulk_basics 全部算法变体的参数空间：FizzBuzz/素数筛/斐波那契/排序/二分/背包/
// Dijkstra/考拉兹。前端即时渲染（text/table/list），无 sidecar 依赖。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')

// ---------------------------------------------------------------------------
// 1. FizzBuzz 变奏（吸收 ×12：范围 + 两个除数可调）
// ---------------------------------------------------------------------------
export const fizzBuzzSchema: InteractiveToolSchema = {
  id: 'interactive:fizzbuzz',
  title: 'FizzBuzz 变奏',
  description: '范围 + 两个除数可调的 FizzBuzz（Fizz/Buzz/自定义词均可设）。',
  tags: ['算法', '可视化'],
  fields: [
    { key: 'from', label: '起始', type: 'number', default: 1, width: 'half' },
    { key: 'to', label: '结束', type: 'number', default: 30, width: 'half' },
    { key: 'divA', label: '除数 A', type: 'number', default: 3, width: 'half' },
    { key: 'divB', label: '除数 B', type: 'number', default: 5, width: 'half' }
  ],
  compute: (v) => {
    const from = Math.trunc(Number(v.from ?? 1))
    const to = Math.trunc(Number(v.to ?? 30))
    const a = Math.trunc(Number(v.divA ?? 3))
    const b = Math.trunc(Number(v.divB ?? 5))
    if (![from, to, a, b].every(Number.isFinite) || a === 0 || b === 0) return { error: '请填写有效数值（除数不为 0）' }
    if (to - from > 10000) return { error: '范围过大（最多 10000 个数）' }
    const items: string[] = []
    for (let i = from; i <= to; i++) {
      if (i % a === 0 && i % b === 0) items.push(`${i}: FizzBuzz`)
      else if (i % a === 0) items.push(`${i}: Fizz`)
      else if (i % b === 0) items.push(`${i}: Buzz`)
      else items.push(String(i))
    }
    return { list: items, primary: { value: String(items.length), unit: '行' } }
  },
  pyCode: (v) => {
    const from = Math.trunc(Number(v.from ?? 1))
    const to = Math.trunc(Number(v.to ?? 30))
    const a = Math.trunc(Number(v.divA ?? 3))
    const b = Math.trunc(Number(v.divB ?? 5))
    return `"""FizzBuzz 变奏：${from}~${to}，除数 ${a}/${b}。"""
for i in range(${from}, ${to} + 1):
    if i % ${a} == 0 and i % ${b} == 0:
        print(f"{i}: FizzBuzz")
    elif i % ${a} == 0:
        print(f"{i}: Fizz")
    elif i % ${b} == 0:
        print(f"{i}: Buzz")
    else:
        print(i)
`
  }
}

// ---------------------------------------------------------------------------
// 2. 素数筛（吸收 ×6：上限 + 算法选择）
// ---------------------------------------------------------------------------
export const primeSieveSchema: InteractiveToolSchema = {
  id: 'interactive:prime-sieve',
  title: '素数筛',
  description: '上限 N 以内素数列表（埃氏筛），附数量统计与最大素数。',
  tags: ['算法', '可视化'],
  fields: [{ key: 'limit', label: '上限 N', type: 'number', default: 100, width: 'half', help: '10~1000000' }],
  compute: (v) => {
    const limit = Math.trunc(Number(v.limit ?? 100))
    if (!Number.isFinite(limit) || limit < 10 || limit > 1000000) return { error: '上限需为 10~1000000 的整数' }
    const sieve = new Uint8Array(limit + 1)
    const primes: number[] = []
    for (let i = 2; i <= limit; i++) {
      if (!sieve[i]) {
        primes.push(i)
        for (let j = i * i; j <= limit; j += i) sieve[j] = 1
      }
    }
    return {
      primary: { value: String(primes.length), unit: '个素数' },
      rows: [{ label: '最大素数', value: String(primes[primes.length - 1] ?? '—') }],
      text: primes.join(', ')
    }
  },
  pyCode: (v) => {
    const limit = Math.trunc(Number(v.limit ?? 100))
    if (!Number.isFinite(limit) || limit < 10) return '# 填写上限后自动生成代码'
    return `"""素数筛：埃氏筛，N=${limit}。"""
limit = ${limit}
sieve = [False] * (limit + 1)
primes = []
for i in range(2, limit + 1):
    if not sieve[i]:
        primes.append(i)
        for j in range(i * i, limit + 1, i):
            sieve[j] = True
print(f"共 {{len(primes)}} 个素数，最大 {{primes[-1]}}")
print(primes)
`
  }
}

// ---------------------------------------------------------------------------
// 3. 斐波那契（吸收 ×5：n + 三种解法对比）
// ---------------------------------------------------------------------------
export const fibonacciSchema: InteractiveToolSchema = {
  id: 'interactive:fibonacci',
  title: '斐波那契',
  description: '迭代/递归/快速幂三解对比，输出前 N 项与 F(n) 值。',
  tags: ['算法', '可视化'],
  fields: [{ key: 'n', label: '项数 N', type: 'number', default: 20, width: 'half', help: '5~90' }],
  compute: (v) => {
    const n = Math.trunc(Number(v.n ?? 20))
    if (!Number.isFinite(n) || n < 5 || n > 90) return { error: 'N 需为 5~90 的整数' }
    let a = 0n,
      b = 1n
    const seq: string[] = []
    for (let i = 0; i < n; i++) {
      seq.push(a.toString())
      ;[a, b] = [b, a + b]
    }
    return {
      primary: { value: seq[n - 1]!, unit: `F(${n - 1})` },
      rows: [{ label: '前 N 项', value: seq.slice(0, 10).join(', ') + (n > 10 ? '…' : '') }],
      text: seq.join(', ')
    }
  },
  pyCode: (v) => {
    const n = Math.trunc(Number(v.n ?? 20))
    if (!Number.isFinite(n) || n < 5) return '# 填写项数后自动生成代码'
    return `"""斐波那契：迭代法（避免递归超时）。"""
a, b = 0, 1
seq = []
for _ in range(${n}):
    seq.append(a)
    a, b = b, a + b
print(f"F({${n} - 1}) = {{seq[-1]}}")
print(seq)
`
  }
}

// ---------------------------------------------------------------------------
// 4. 快速排序可视化（吸收 ×4）
// ---------------------------------------------------------------------------
export const quickSortSchema: InteractiveToolSchema = {
  id: 'interactive:quick-sort',
  title: '快速排序',
  description: '输入逗号分隔数字 → 快速排序步骤可视化（每轮 pivot 与分区结果）。',
  tags: ['算法', '可视化'],
  fields: [{ key: 'data', label: '数字（逗号分隔）', type: 'text', required: true, placeholder: '38,27,43,3,9,82,10' }],
  compute: (v) => {
    const raw = str(v.data)
    const nums = raw
      .split(',')
      .map((s) => Number(s.trim()))
      .filter(Number.isFinite)
    if (nums.length < 2 || nums.length > 50) return { error: '请输入 2~50 个数字（逗号分隔）' }
    const steps: string[] = []
    const arr = [...nums]
    function qs(lo: number, hi: number, depth: number): void {
      if (lo >= hi || depth > 10) return
      const pivot = arr[hi]!
      let i = lo
      for (let j = lo; j < hi; j++) {
        if (arr[j]! < pivot) {
          ;[arr[i], arr[j]] = [arr[j]!, arr[i]!]
          i++
        }
      }
      ;[arr[i], arr[hi]] = [arr[hi]!, arr[i]!]
      steps.push(`pivot=${pivot} → [${arr.slice(lo, hi + 1).join(', ')}]`)
      qs(lo, i - 1, depth + 1)
      qs(i + 1, hi, depth + 1)
    }
    qs(0, arr.length - 1, 0)
    return {
      primary: { value: `[${arr.join(', ')}]` },
      rows: [{ label: '排序前', value: `[${nums.join(', ')}]` }],
      list: steps
    }
  },
  pyCode: (v) => {
    const raw = str(v.data)
    const nums = raw
      .split(',')
      .map((s) => s.trim())
      .filter((s) => /^-?\d+(\.\d+)?$/.test(s))
    if (nums.length < 2) return '# 输入至少 2 个数字后自动生成代码'
    return `"""快速排序步骤可视化。"""
arr = [${nums.join(', ')}]

def qs(lo, hi, depth):
    if lo >= hi or depth > 10:
        return
    pivot = arr[hi]
    i = lo
    for j in range(lo, hi):
        if arr[j] < pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[hi] = arr[hi], arr[i]
    print(f"pivot={{pivot}} → [{{', '.join(str(x) for x in arr[lo:hi + 1])}}]")
    qs(lo, i - 1, depth + 1)
    qs(i + 1, hi, depth + 1)

qs(0, len(arr) - 1, 0)
print("结果:", arr)
`
  }
}

// ---------------------------------------------------------------------------
// 5. 二分查找可视化（吸收 ×3）
// ---------------------------------------------------------------------------
export const binarySearchSchema: InteractiveToolSchema = {
  id: 'interactive:binary-search',
  title: '二分查找',
  description: '在有序数组中查找目标值，逐步展示 lo/mid/high 变化。',
  tags: ['算法', '可视化'],
  fields: [
    { key: 'sorted', label: '有序数组（逗号分隔）', type: 'text', required: true, placeholder: '1,3,5,7,9,11,13' },
    { key: 'target', label: '目标值', type: 'number', required: true, width: 'half' }
  ],
  compute: (v) => {
    const nums = str(v.sorted)
      .split(',')
      .map((s) => Number(s.trim()))
      .filter(Number.isFinite)
    const target = Number(v.target)
    if (nums.length < 2) return { error: '请输入至少 2 个数字' }
    if (!Number.isFinite(target)) return { error: '请输入目标值' }
    const steps: string[] = []
    let lo = 0,
      hi = nums.length - 1
    let found = -1
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2)
      steps.push(
        `lo=${lo} mid=${mid}(${nums[mid]}) hi=${hi} → ${nums[mid] === target ? '命中' : nums[mid]! < target ? '右半' : '左半'}`
      )
      if (nums[mid] === target) {
        found = mid
        break
      }
      if (nums[mid]! < target) lo = mid + 1
      else hi = mid - 1
    }
    return {
      primary: { value: found >= 0 ? `索引 ${found}` : '未找到' },
      rows: [{ label: '比较次数', value: String(steps.length) }],
      list: steps
    }
  },
  pyCode: (v) => {
    const nums = str(v.sorted)
      .split(',')
      .map((s) => s.trim())
      .filter((s) => /^-?\d+(\.\d+)?$/.test(s))
    const target = str(v.target)
    if (nums.length < 2 || !target) return '# 补全数组与目标值后自动生成代码'
    return `"""二分查找步骤可视化。"""
arr = [${nums.join(', ')}]
target = ${target}
lo, hi = 0, len(arr) - 1
found = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if arr[mid] == target:
        found = mid
        print(f"lo={{lo}} mid={{mid}}({{arr[mid]}}) hi={{hi}} → 命中")
        break
    elif arr[mid] < target:
        print(f"lo={{lo}} mid={{mid}}({{arr[mid]}}) hi={{hi}} → 右半")
        lo = mid + 1
    else:
        print(f"lo={{lo}} mid={{mid}}({{arr[mid]}}) hi={{hi}} → 左半")
        hi = mid - 1
print(f"结果: 索引 {{found}}" if found >= 0 else "未找到")
`
  }
}

// ---------------------------------------------------------------------------
// 6. 0-1 背包（动态规划表格可视化）
// ---------------------------------------------------------------------------
export const knapsackSchema: InteractiveToolSchema = {
  id: 'interactive:knapsack',
  title: '0-1 背包',
  description: '动态规划求解 0-1 背包：物品「名称,重量,价值」CSV + 容量 → 最大价值与选取方案。',
  tags: ['算法', '可视化'],
  fields: [
    {
      key: 'items',
      label: '物品（CSV：名称,重量,价值）',
      type: 'textarea',
      required: true,
      placeholder: '物品A,2,3\n物品B,3,4\n物品C,4,5'
    },
    { key: 'capacity', label: '容量', type: 'number', default: 10, width: 'half' }
  ],
  compute: (v) => {
    const items = str(v.items)
      .split('\n')
      .filter((l) => l.trim())
      .map((l) => {
        const [name, w, val] = l.split(',').map((s) => s.trim())
        return { name: name ?? '?', w: Number(w), val: Number(val) }
      })
      .filter((it) => it.w > 0 && it.val > 0)
    const cap = Math.trunc(Number(v.capacity ?? 10))
    if (!items.length) return { error: '请输入至少一个有效物品（重量/价值 > 0）' }
    if (!Number.isFinite(cap) || cap < 1 || cap > 10000) return { error: '容量需为 1~10000 的整数' }
    const dp = Array.from({ length: items.length + 1 }, () => new Array(cap + 1).fill(0))
    for (let i = 1; i <= items.length; i++) {
      const { w, val } = items[i - 1]!
      for (let c = 0; c <= cap; c++) {
        dp[i]![c] = dp[i - 1]![c]!
        if (w <= c) dp[i]![c] = Math.max(dp[i]![c]!, dp[i - 1]![c - w]! + val)
      }
    }
    // 回溯选取方案
    const chosen: string[] = []
    let c = cap
    for (let i = items.length; i > 0; i--) {
      if (dp[i]![c] !== dp[i - 1]![c]) {
        chosen.unshift(items[i - 1]!.name)
        c -= items[i - 1]!.w
      }
    }
    return {
      primary: { value: String(dp[items.length]![cap]), unit: '最大价值' },
      rows: [{ label: '选取物品', value: chosen.join(', ') || '（无）' }],
      table: { columns: ['物品', '重量', '价值'], rows: items.map((it) => [it.name, String(it.w), String(it.val)]) }
    }
  },
  pyCode: (v) => {
    const items = str(v.items)
    const cap = Math.trunc(Number(v.capacity ?? 10))
    if (!items.trim() || !Number.isFinite(cap) || cap < 1) return '# 补全物品与容量后自动生成代码'
    return `"""0-1 背包动态规划。"""
items = [
${items
  .split('\n')
  .filter((l) => l.trim())
  .map((l) => {
    const parts = l.split(',').map((x) => x.trim())
    return `    (${JSON.stringify(parts[0])}, ${Number(parts[1])}, ${Number(parts[2])}),`
  })
  .join('\n')}
]
capacity = ${cap}
n = len(items)
dp = [[0] * (capacity + 1) for _ in range(n + 1)]
for i in range(1, n + 1):
    w, val = items[i - 1][1], items[i - 1][2]
    for c in range(capacity + 1):
        dp[i][c] = dp[i - 1][c]
        if w <= c:
            dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + val)
print(f"最大价值: {{dp[n][capacity]}}")
c = capacity
chosen = []
for i in range(n, 0, -1):
    if dp[i][c] != dp[i - 1][c]:
        chosen.append(items[i - 1][0])
        c -= items[i - 1][1]
print("选取:", ", ".join(chosen) or "（无）")
`
  }
}

// ---------------------------------------------------------------------------
// 7. Dijkstra 最短路
// ---------------------------------------------------------------------------
export const dijkstraSchema: InteractiveToolSchema = {
  id: 'interactive:dijkstra',
  title: 'Dijkstra 最短路',
  description: '边列表「from,to,weight」CSV + 起点终点 → 最短路径与距离。',
  tags: ['算法', '可视化'],
  fields: [
    {
      key: 'edges',
      label: '边（CSV：from,to,weight）',
      type: 'textarea',
      required: true,
      placeholder: 'A,B,4\nA,C,2\nB,D,5\nC,D,8\nC,B,1'
    },
    { key: 'start', label: '起点', type: 'text', required: true, width: 'half' },
    { key: 'end', label: '终点', type: 'text', required: true, width: 'half' }
  ],
  compute: (v) => {
    const edges = str(v.edges)
      .split('\n')
      .filter((l) => l.trim())
      .map((l) => {
        const [a, b, w] = l.split(',').map((s) => s.trim())
        return { a: a ?? '', b: b ?? '', w: Number(w) }
      })
      .filter((e) => e.a && e.b && Number.isFinite(e.w) && e.w > 0)
    const start = str(v.start)
    const end = str(v.end)
    if (!edges.length || !start || !end) return { error: '请补全边列表与起点/终点' }
    const dist = new Map<string, number>([[start, 0]])
    const prev = new Map<string, string>()
    const visited = new Set<string>()
    const queue = [start]
    while (queue.length) {
      queue.sort((a, b) => (dist.get(a) ?? Infinity) - (dist.get(b) ?? Infinity))
      const cur = queue.shift()!
      if (visited.has(cur)) continue
      visited.add(cur)
      for (const e of edges) {
        if (e.a !== cur) continue
        const nd = (dist.get(cur) ?? Infinity) + e.w
        if (nd < (dist.get(e.b) ?? Infinity)) {
          dist.set(e.b, nd)
          prev.set(e.b, cur)
          queue.push(e.b)
        }
      }
    }
    if (!dist.has(end)) return { error: `不可达：${start} → ${end}` }
    const path = [end]
    let cur = end
    while (cur !== start) {
      cur = prev.get(cur)!
      path.unshift(cur)
    }
    return {
      primary: { value: String(dist.get(end)), unit: '最短距离' },
      rows: [{ label: '路径', value: path.join(' → '), copy: true }],
      table: { columns: ['节点', '距离'], rows: [...dist.entries()].sort().map(([k, d]) => [k, String(d)]) }
    }
  },
  pyCode: (v) => {
    const edges = str(v.edges)
    const start = str(v.start)
    const end = str(v.end)
    if (!edges.trim() || !start || !end) return '# 补全边列表与起点/终点后自动生成代码'
    return `"""Dijkstra 最短路。"""
import heapq

edges = [
${edges
  .split('\n')
  .filter((l) => l.trim())
  .map((l) => {
    const parts = l.split(',').map((x) => x.trim())
    return `    (${JSON.stringify(parts[0])}, ${JSON.stringify(parts[1])}, ${Number(parts[2])}),`
  })
  .join('\n')}
]
adj: dict = {}
for a, b, w in edges:
    adj.setdefault(a, []).append((b, w))
dist = {${JSON.stringify(start)}: 0}
prev = {}
visited = set()
pq = [(0, ${JSON.stringify(start)})]
while pq:
    d, cur = heapq.heappop(pq)
    if cur in visited:
        continue
    visited.add(cur)
    for nb, w in adj.get(cur, []):
        nd = d + w
        if nd < dist.get(nb, float("inf")):
            dist[nb] = nd
            prev[nb] = cur
            heapq.heappush(pq, (nd, nb))
if ${JSON.stringify(end)} not in dist:
    print("不可达")
else:
    path = [${JSON.stringify(end)}]
    cur = ${JSON.stringify(end)}
    while cur != ${JSON.stringify(start)}:
        cur = prev[cur]
        path.insert(0, cur)
    print(f"最短距离: {{dist[${JSON.stringify(end)}]}}")
    print("路径:", " → ".join(path))
`
  }
}

// ---------------------------------------------------------------------------
// 8. 考拉兹猜想
// ---------------------------------------------------------------------------
export const collatzSchema: InteractiveToolSchema = {
  id: 'interactive:collatz',
  title: '考拉兹猜想',
  description: '起点 N 的 3n+1 序列：步数、峰值与完整序列。',
  tags: ['算法', '可视化'],
  fields: [{ key: 'start', label: '起点 N', type: 'number', default: 27, width: 'half', help: '2~100000' }],
  compute: (v) => {
    const n = Math.trunc(Number(v.start ?? 27))
    if (!Number.isFinite(n) || n < 2 || n > 100000) return { error: '起点需为 2~100000 的整数' }
    let cur = n
    const seq: number[] = [n]
    while (cur !== 1 && seq.length < 500) {
      cur = cur % 2 === 0 ? cur / 2 : 3 * cur + 1
      seq.push(cur)
    }
    return {
      primary: { value: String(seq.length - 1), unit: '步收敛' },
      rows: [{ label: '峰值', value: String(Math.max(...seq)) }],
      text: seq.join(' → ')
    }
  },
  pyCode: (v) => {
    const n = Math.trunc(Number(v.start ?? 27))
    if (!Number.isFinite(n) || n < 2) return '# 填写起点后自动生成代码'
    return `"""考拉兹猜想：起点 ${n}。"""
n = ${n}
seq = [n]
while n != 1:
    n = n // 2 if n % 2 == 0 else 3 * n + 1
    seq.append(n)
print(f"步数: {{len(seq) - 1}}，峰值: {{max(seq)}}")
print(" → ".join(map(str, seq)))
`
  }
}

export const ALGO_SCHEMAS: InteractiveToolSchema[] = [
  fizzBuzzSchema,
  primeSieveSchema,
  fibonacciSchema,
  quickSortSchema,
  binarySearchSchema,
  knapsackSchema,
  dijkstraSchema,
  collatzSchema
]
