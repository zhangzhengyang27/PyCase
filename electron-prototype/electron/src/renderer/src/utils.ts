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
// 质量分徽章配色（0-100，六维质量评分总分）——状态令牌见 theme.css
// ---------------------------------------------------------------------------
export function qualityBadgeCls(score: number | undefined): string {
  const s = score ?? 0
  if (s >= 80) return 'bg-ok-bg text-ok'
  if (s >= 60) return 'bg-warn-bg text-warn'
  return 'bg-hover text-ink-mute'
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
  risky: '高危'
}

export function runStatusLabel(status: string | undefined): string {
  return (status && RUN_STATUS_LABELS[status]) || ''
}

export function runStatusBadgeCls(status: string | undefined): string {
  switch (status) {
    case 'missing_deps':
      return 'bg-warn-bg text-warn'
    case 'empty':
    case 'broken':
      return 'bg-hover text-ink-mute'
    case 'risky':
      return 'bg-danger-bg text-danger'
    default:
      return ''
  }
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

// 按钮基类（带 subtle 边框、5px/12px 内边距）
const BTN_BASE_CLS =
  "inline-flex items-center gap-1 px-3 py-[5px] border border-line-subtle rounded-md bg-transparent text-[12px] font-[510] font-sans cursor-pointer whitespace-nowrap tracking-[-0.005em] leading-[1.4] transition-all duration-[120ms] active:scale-[0.97] disabled:opacity-[0.35] disabled:cursor-not-allowed";
export const BTN_GHOST_CLS = `${BTN_BASE_CLS} text-ink-dim hover:bg-hover hover:text-ink`;
export const BTN_PRIMARY_CLS = `${BTN_BASE_CLS} bg-accent border-accent text-white shadow-elev-1 enabled:hover:bg-accent-hover enabled:hover:shadow-elev-2`;
export const BTN_DANGER_CLS = `${BTN_BASE_CLS} bg-danger text-white enabled:hover:opacity-90`;

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

// 主题视图运行状态徽章（代替状态点）
const THEME_STATUS_BASE = 'inline-block px-2 py-px rounded-full text-[11px] leading-[1.6] font-[510] bg-[rgba(127,127,127,0.12)]'
export const THEME_STATUS_CLS = {
  idle: `${THEME_STATUS_BASE} text-ink-mute`,
  running: 'inline-block px-2 py-px rounded-full text-[11px] leading-[1.6] font-[510] bg-[rgba(64,128,255,0.14)] text-[#4080ff]',
  success: 'inline-block px-2 py-px rounded-full text-[11px] leading-[1.6] font-[510] bg-[rgba(52,199,89,0.14)] text-ok',
  error: 'inline-block px-2 py-px rounded-full text-[11px] leading-[1.6] font-[510] bg-[rgba(255,59,48,0.14)] text-danger'
} as const

// 工具卡片图标：按脚本文件名关键词映射（emoji 体系，v0.10 卡片内联 HTML 使用）
const TOOL_ICON_RULES: Array<[RegExp, string]> = [
  [/bili|video|movie|douyin|tiktok/i, "📺"],
  [/crawl|spider|scrape|comment|weibo|weather|news/i, "🕸️"],
  [/download|fetch/i, "⬇️"],
  [/image|pic|photo|compress|watermark|crop/i, "🖼️"],
  [/pdf|word|office|excel|docx/i, "📄"],
  [/mail|email/i, "📧"],
  [/music|audio|mp3/i, "🎵"],
  [/translate|nlp|text/i, "🌐"],
  [/rename|file|dir/i, "📁"],
  [/password|token|secret|encrypt/i, "🔐"],
  [/timer|todo|schedule/i, "⏱️"],
  [/chart|plot|viz|data/i, "📊"],
]

export function getToolIcon(name: string): string {
  for (const [re, icon] of TOOL_ICON_RULES) {
    if (re.test(name)) return icon
  }
  return "🛠️"
}

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
