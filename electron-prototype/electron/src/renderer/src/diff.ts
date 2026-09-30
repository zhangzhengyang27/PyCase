// diff.ts：行级差异（编辑历史「与当前版本对比」用；纯函数，无 DOM 依赖）。
//
// 用经典 LCS 动态规划：示例源码量级（几十到几百行）下开销可忽略，
// 换来的是"最小编辑"语义的行对齐——比逐行位置比较可靠得多（插入一行不会让整段全红）。

export type DiffKind = 'same' | 'add' | 'del'

export interface DiffLine {
  kind: DiffKind
  text: string
  /** 原文件（左）行号，1 起；add 行为 null */
  left: number | null
  /** 新文件（右）行号，1 起；del 行为 null */
  right: number | null
}

/** 行级差异：left = 历史版本，right = 当前内容。 */
export function diffLines(left: string, right: string): DiffLine[] {
  // 空串 = 没有行（而不是"一个空行"）：空文件的历史版本在面板里应当是"0 行"
  const a = left === '' ? [] : left.split('\n')
  const b = right === '' ? [] : right.split('\n')
  const n = a.length
  const m = b.length
  // lcs[i][j] = a[i:] 与 b[j:] 的最长公共子序列长度
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }
  const out: DiffLine[] = []
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ kind: 'same', text: a[i], left: i + 1, right: j + 1 })
      i++
      j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      out.push({ kind: 'del', text: a[i], left: i + 1, right: null })
      i++
    } else {
      out.push({ kind: 'add', text: b[j], left: null, right: j + 1 })
      j++
    }
  }
  while (i < n) {
    out.push({ kind: 'del', text: a[i], left: i + 1, right: null })
    i++
  }
  while (j < m) {
    out.push({ kind: 'add', text: b[j], left: null, right: j + 1 })
    j++
  }
  return out
}

/** 差异统计（面板头部用）。 */
export function diffStats(lines: DiffLine[]): { added: number; removed: number } {
  let added = 0
  let removed = 0
  for (const l of lines) {
    if (l.kind === 'add') added++
    else if (l.kind === 'del') removed++
  }
  return { added, removed }
}
