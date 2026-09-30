// monaco.ts：Monaco 初始化（从旧 monaco-editor.ts 移植，Vue 化）
// ESM + worker 模式（与 CSP 兼容，不走 CDN）；主题色读 CSS 变量，随 data-theme 切换。
// 代码区跟随主题（A1 §3.2）：底色 --bg-console，语法色 --code-*，与页稿/终端同一套。
import * as monaco from 'monaco-editor/editor/editor.api'
import 'monaco-editor/languages/definitions/python/register'
import editorWorker from 'monaco-editor/editor/editor.worker?worker'

self.MonacoEnvironment = {
  getWorker() {
    return new editorWorker()
  }
}

// Helper: read CSS variable at runtime (no hardcoded colors)
const cssVar = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

// CSS 颜色 → 规范化。构建产物会把 #ffffff 压成 #fff，而 Monaco 只接受 6/8 位十六进制
// （否则抛 Illegal value for token color）；同时兼容 rgba() 形式的令牌。
function toRgba(value: string): [number, number, number, number] {
  const v = value.trim()
  if (v.startsWith('#')) {
    let h = v.slice(1)
    // 支持 #rgb / #rgba / #rrggbb / #rrggbbaa——构建产物会把 rgba() 压成 8 位十六进制，
    // 早先只认 6 位会把 alpha 当 1，5% 的行高亮因此渲染成纯黑
    if (h.length === 3 || h.length === 4)
      h = h
        .split('')
        .map((c) => c + c)
        .join('')
    const n = parseInt(h.slice(0, 6), 16) || 0
    const a = h.length >= 8 ? (parseInt(h.slice(6, 8), 16) || 0) / 255 : 1
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, a]
  }
  const m = v.match(/rgba?\(([^)]+)\)/)
  if (m) {
    const parts = m[1].split(',').map((p) => parseFloat(p))
    return [parts[0] || 0, parts[1] || 0, parts[2] || 0, parts.length > 3 ? parts[3] : 1]
  }
  return [0, 0, 0, 1]
}

const toHex = (c: number) => Math.round(c).toString(16).padStart(2, '0')

/** 令牌 → Monaco 颜色（#rrggbb，不透明） */
const color = (name: string): string => {
  const [r, g, b] = toRgba(cssVar(name))
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

/** 半透明令牌 → Monaco 颜色：先按 alpha 合成到底色上。
    Monaco 的主题色只按 6 位十六进制取色（8 位会丢掉 alpha 变成不透明），
    直接给 rgba()/8 位值会把 5% 的行高亮渲染成纯黑（A4 走查发现）。 */
const over = (name: string, base: string, alpha?: number): string => {
  const [r, g, b, a] = toRgba(cssVar(name))
  const k = alpha ?? a
  const [br, bg, bb] = toRgba(cssVar(base))
  const mix = (c: number, bc: number) => Math.round(c * k + bc * (1 - k))
  return `#${toHex(mix(r, br))}${toHex(mix(g, bg))}${toHex(mix(b, bb))}`
}

// 主题定义每次 apply 都重新注册：CSS 变量在 define 时取值快照，
// 若只 define 一次，从 light 切到 dark 时 dark 定义仍带着 light 期变量值
// 两套主题共用一份规则/取色表：底色、语法色、控件色全部来自 v2 令牌，
// 深浅差异由令牌的值承担，不再各写一份字面量
const RULES = [
  { token: 'comment', foreground: color('--code-cmt'), fontStyle: 'italic' },
  { token: 'keyword', foreground: color('--code-kw') },
  { token: 'string', foreground: color('--code-str') },
  { token: 'number', foreground: color('--code-num') },
  { token: 'type', foreground: color('--code-kw') },
  { token: 'function', foreground: color('--code-fn') },
  { token: 'variable', foreground: color('--text-console') },
  { token: 'operator', foreground: color('--text-console') },
  { token: 'delimiter', foreground: color('--text-console') },
  { token: 'regexp', foreground: color('--code-str') },
  { token: 'constant', foreground: color('--code-num') },
  { token: 'attribute.name', foreground: color('--code-kw') },
  { token: 'attribute.value', foreground: color('--code-str') }
]

function editorColors(): Record<string, string> {
  return {
    'editor.background': color('--bg-console'),
    'editor.foreground': color('--text-console'),
    'editor.lineHighlightBackground': over('--bg-hover', '--bg-console'),
    'editorLineNumber.foreground': color('--text-gutter'),
    'editorLineNumber.activeForeground': color('--text-console'),
    'editor.selectionBackground': over('--accent', '--bg-console', 0.25),
    'editor.inactiveSelectionBackground': over('--accent', '--bg-console', 0.12),
    'editorIndentGuide.background': over('--line-hairline', '--bg-console'),
    'editorIndentGuide.activeBackground': over('--line-strong', '--bg-console'),
    'editorWidget.background': color('--bg-card'),
    'editorWidget.border': over('--line-hairline', '--bg-card'),
    'editorSuggestWidget.background': color('--bg-card'),
    'editorSuggestWidget.border': over('--line-hairline', '--bg-card'),
    'editorSuggestWidget.selectedBackground': over('--accent', '--bg-card', 0.15),
    'editorCursor.foreground': color('--accent'),
    'editor.findMatchBackground': over('--accent', '--bg-console', 0.3),
    'editor.findMatchHighlightBackground': over('--accent', '--bg-console', 0.15),
    'scrollbarSlider.background': over('--text-console', '--bg-console', 0.1),
    'scrollbarSlider.hoverBackground': over('--text-console', '--bg-console', 0.18),
    'scrollbarSlider.activeBackground': over('--text-console', '--bg-console', 0.25),
    'editorGutter.background': color('--bg-console'),
    'editorOverviewRuler.border': over('--line-hairline', '--bg-console')
  }
}

function defineThemes(): void {
  monaco.editor.defineTheme('pycase-dark', { base: 'vs-dark', inherit: true, rules: RULES, colors: editorColors() })
  monaco.editor.defineTheme('pycase-light', { base: 'vs', inherit: true, rules: RULES, colors: editorColors() })
}

export function currentMonacoTheme(): string {
  const t = document.documentElement.getAttribute('data-theme') || 'dark'
  return t === 'dark' ? 'pycase-dark' : 'pycase-light'
}

export function applyMonacoTheme(): void {
  defineThemes()
  monaco.editor.setTheme(currentMonacoTheme())
}

export { monaco }
