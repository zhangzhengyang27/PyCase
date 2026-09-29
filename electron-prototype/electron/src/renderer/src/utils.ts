// utils.ts：纯函数工具集（无副作用、无全局依赖，可独立测试）
// 注意：本文件会被 node 单测直接加载，不引入组件库（图标映射见 src/icons.ts）。

// ---------------------------------------------------------------------------
// 侧栏连接状态点（工具栏 8px；底部状态栏 6px 用 statusDotCls(…, 'sm')）
// ---------------------------------------------------------------------------
export function statusDotCls(state: 'connecting' | 'ready' | 'error', size: 'md' | 'sm' = 'md'): string {
  const box = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2'
  const color = state === 'connecting' ? 'bg-warn animate-pulse' : state === 'ready' ? 'bg-ok' : 'bg-danger'
  return `inline-block ${box} rounded-full shrink-0 ${color}`
}

// ---------------------------------------------------------------------------
// 文件大小格式化：字节 → 人类可读格式
// ---------------------------------------------------------------------------
export function formatFileSize(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

// ---------------------------------------------------------------------------
// 单行命令行参数拆分（shlex 简化版）：空格分隔，单/双引号成组，支持空串参数
// 运行器视图的「单行参数输入框」使用；纯函数可独立测试
// ---------------------------------------------------------------------------
export function splitArgs(line: string): string[] {
  const tokens: string[] = []
  let cur = ''
  let quote: string | null = null
  let quoted = false
  for (const ch of line || '') {
    if (quote) {
      if (ch === quote) {
        quote = null
      } else {
        cur += ch
      }
    } else if (ch === '"' || ch === "'") {
      quote = ch
      quoted = true
    } else if (ch === ' ' || ch === '\t') {
      if (quoted || cur) {
        tokens.push(cur)
        cur = ''
        quoted = false
      }
    } else {
      cur += ch
    }
  }
  if (quoted || cur) tokens.push(cur)
  return tokens
}

// ---------------------------------------------------------------------------
// 质量分文字配色（0-100，六维质量评分总分）
// v2：分数不再用底色徽章，按档取文字色——低分才是信号，及格以上保持中性
// ---------------------------------------------------------------------------
export function qualityTextCls(score: number | undefined): string {
  return (score ?? 0) < 60 ? 'text-warn' : 'text-ink-mute'
}

// ---------------------------------------------------------------------------
// 可运行性状态徽章：文案与配色（sidecar run_status 派生字段）。
// runnable 无需徽章（正向状态不占视觉空间）；risky 由高危徽章承担展示。
// ---------------------------------------------------------------------------
const RUN_STATUS_LABELS: Record<string, string> = {
  runnable: '可运行',
  missing_deps: '缺依赖',
  empty: '空壳',
  broken: '语法损坏',
  risky: '高危',
  // 扫描器自身异常：不假定可运行（C3 不 fail-open），但也不误报为高危
  unknown: '状态未知'
}

export function runStatusLabel(status: string | undefined): string {
  return (status && RUN_STATUS_LABELS[status]) || ''
}

/** 状态圆点配色（v2 状态语言 = 彩色圆点 + 中性文字；仅高危保留红字） */
const RUN_STATUS_DOT: Record<string, string> = {
  runnable: 'bg-ok',
  missing_deps: 'bg-warn',
  empty: 'bg-ink-faint',
  broken: 'bg-ink-faint',
  risky: 'bg-danger',
  unknown: 'bg-ink-faint'
}

export function runStatusDotCls(status: string | undefined): string {
  return (status && RUN_STATUS_DOT[status]) || 'bg-ink-faint'
}

export function runStatusTextCls(status: string | undefined): string {
  return status === 'risky' ? 'text-danger' : 'text-ink-mute'
}

/** 卡片/详情页状态徽章的悬浮提示文案 */
export function runStatusHint(status: string | undefined): string {
  switch (status) {
    case 'missing_deps':
      return '依赖的第三方库在共享运行环境中缺失，运行会因 ImportError 失败'
    case 'empty':
      return '空壳示例：去除 docstring 后没有有效代码'
    case 'broken':
      return '代码存在语法错误，无法运行'
    case 'risky':
      return '含高危操作（系统命令/文件删除等），运行前请先审阅代码；子进程隔离不是安全沙箱'
    case 'runnable':
      return '静态检查通过，推定可运行（不保证运行结果符合预期）'
    default:
      return ''
  }
}

// ---------------------------------------------------------------------------
// Tailwind 类名常量：JS 会整体替换 className 的元素必须在这里给出完整工具类串
// （JS 赋值 className 会覆盖 HTML 上的静态工具类，散落字面量容易漏基础类）
// ---------------------------------------------------------------------------


// 输出面板状态点（8px，默认灰）
export const OUTPUT_DOT_CLS = {
  idle: 'inline-block w-2 h-2 rounded-full shrink-0 bg-ink-faint',
  running: 'inline-block w-2 h-2 rounded-full shrink-0 bg-warn animate-pulse',
  success: 'inline-block w-2 h-2 rounded-full shrink-0 bg-ok',
  error: 'inline-block w-2 h-2 rounded-full shrink-0 bg-danger'
} as const

// 输出行（示例库终端与主题抽屉共用）
export const OUTPUT_LINE_CLS = {
  base: 'whitespace-pre-wrap break-all text-ink-dim',
  system: 'whitespace-pre-wrap break-all text-ink-faint italic text-[11px]',
  error: 'whitespace-pre-wrap break-all text-danger',
  success: 'whitespace-pre-wrap break-all text-ok'
} as const

// ---------------------------------------------------------------------------
// HTML 转义：防止 XSS，所有用户/示例数据插入 DOM 前必须经过此函数。
// 纯字符串替换（不建 DOM 节点）：渲染热路径每次筛选调用数百次；
// 引号必须转义——textContent/innerHTML 技巧不转义引号，属性位置
// data-x="${...}" 可被值中的 " 突破注入 onerror 等事件处理器。
// ---------------------------------------------------------------------------
export function escapeHtml(str: unknown): string {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
