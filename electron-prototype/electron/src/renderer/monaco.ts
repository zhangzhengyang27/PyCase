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
const hex = (name: string) => cssVar(name).replace('#', '')
const rgba = (name: string, alpha: number) => {
  const h = cssVar(name).replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

// 主题定义每次 apply 都重新注册：CSS 变量在 define 时取值快照，
// 若只 define 一次，从 light 切到 dark 时 dark 定义仍带着 light 期变量值
// 两套主题共用一份规则/取色表：底色、语法色、控件色全部来自 v2 令牌，
// 深浅差异由令牌的值承担，不再各写一份字面量
const RULES = [
  { token: 'comment', foreground: hex('--code-cmt'), fontStyle: 'italic' },
  { token: 'keyword', foreground: hex('--code-kw') },
  { token: 'string', foreground: hex('--code-str') },
  { token: 'number', foreground: hex('--code-num') },
  { token: 'type', foreground: hex('--code-kw') },
  { token: 'function', foreground: hex('--code-fn') },
  { token: 'variable', foreground: hex('--text-console') },
  { token: 'operator', foreground: hex('--text-console') },
  { token: 'delimiter', foreground: hex('--text-console') },
  { token: 'regexp', foreground: hex('--code-str') },
  { token: 'constant', foreground: hex('--code-num') },
  { token: 'attribute.name', foreground: hex('--code-kw') },
  { token: 'attribute.value', foreground: hex('--code-str') }
]

function editorColors(): Record<string, string> {
  return {
    'editor.background': cssVar('--bg-console'),
    'editor.foreground': cssVar('--text-console'),
    'editor.lineHighlightBackground': cssVar('--bg-hover'),
    'editorLineNumber.foreground': cssVar('--text-gutter'),
    'editorLineNumber.activeForeground': cssVar('--text-console'),
    'editor.selectionBackground': rgba('--accent', 0.25),
    'editor.inactiveSelectionBackground': rgba('--accent', 0.12),
    'editorIndentGuide.background': cssVar('--line-hairline'),
    'editorIndentGuide.activeBackground': cssVar('--line-strong'),
    'editorWidget.background': cssVar('--bg-card'),
    'editorWidget.border': cssVar('--line-hairline'),
    'editorSuggestWidget.background': cssVar('--bg-card'),
    'editorSuggestWidget.border': cssVar('--line-hairline'),
    'editorSuggestWidget.selectedBackground': rgba('--accent', 0.15),
    'editorCursor.foreground': cssVar('--accent'),
    'editor.findMatchBackground': rgba('--accent', 0.3),
    'editor.findMatchHighlightBackground': rgba('--accent', 0.15),
    'scrollbarSlider.background': rgba('--text-console', 0.1),
    'scrollbarSlider.hoverBackground': rgba('--text-console', 0.18),
    'scrollbarSlider.activeBackground': rgba('--text-console', 0.25),
    'editorGutter.background': cssVar('--bg-console'),
    'editorOverviewRuler.border': cssVar('--line-hairline')
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
