// monaco.ts：Monaco 初始化（从旧 monaco-editor.ts 移植，Vue 化）
// ESM + worker 模式（与 CSP 兼容，不走 CDN）；主题色读 CSS 变量，随 data-theme 切换。
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

let themesDefined = false

function defineThemes(): void {
  if (themesDefined) return
  themesDefined = true

  // Linear inspired dark theme for Monaco — all colors read from CSS variables
  monaco.editor.defineTheme('linear-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: hex('--text-quaternary'), fontStyle: 'italic' },
      { token: 'keyword', foreground: hex('--accent-violet') },
      { token: 'string', foreground: hex('--status-green') },
      { token: 'number', foreground: hex('--status-amber') },
      { token: 'type', foreground: hex('--text-tertiary') },
      { token: 'function', foreground: hex('--text-secondary') },
      { token: 'variable', foreground: hex('--text-primary') },
      { token: 'operator', foreground: hex('--text-tertiary') },
      { token: 'delimiter', foreground: hex('--text-tertiary') },
      { token: 'regexp', foreground: hex('--status-amber') },
      { token: 'constant', foreground: hex('--accent-violet') },
      { token: 'attribute.name', foreground: hex('--accent-violet') },
      { token: 'attribute.value', foreground: hex('--status-green') }
    ],
    colors: {
      'editor.background': cssVar('--bg-marketing'),
      'editor.foreground': cssVar('--text-secondary'),
      'editor.lineHighlightBackground': cssVar('--bg-level3'),
      'editorLineNumber.foreground': cssVar('--border-tertiary'),
      'editorLineNumber.activeForeground': cssVar('--text-tertiary'),
      'editor.selectionBackground': rgba('--brand-indigo', 0.25),
      'editor.inactiveSelectionBackground': rgba('--brand-indigo', 0.12),
      'editorIndentGuide.background': cssVar('--line-tint'),
      'editorIndentGuide.activeBackground': cssVar('--border-primary'),
      'editorWidget.background': cssVar('--bg-panel'),
      'editorWidget.border': rgba('--text-primary', 0.08),
      'editorSuggestWidget.background': cssVar('--bg-panel'),
      'editorSuggestWidget.border': rgba('--text-primary', 0.08),
      'editorSuggestWidget.selectedBackground': rgba('--brand-indigo', 0.15),
      'editorCursor.foreground': cssVar('--accent-violet'),
      'editor.findMatchBackground': rgba('--brand-indigo', 0.3),
      'editor.findMatchHighlightBackground': rgba('--brand-indigo', 0.15),
      'scrollbarSlider.background': rgba('--text-primary', 0.1),
      'scrollbarSlider.hoverBackground': rgba('--text-primary', 0.18),
      'scrollbarSlider.activeBackground': rgba('--text-primary', 0.25),
      'editorGutter.background': cssVar('--bg-marketing'),
      'editorOverviewRuler.border': rgba('--text-primary', 0.05)
    }
  })

  // Linear inspired light theme for Monaco
  monaco.editor.defineTheme('linear-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '8a8f98', fontStyle: 'italic' },
      { token: 'keyword', foreground: '7170ff' },
      { token: 'string', foreground: '27a644' },
      { token: 'number', foreground: 'f5a524' },
      { token: 'type', foreground: '62666d' },
      { token: 'function', foreground: '28282c' },
      { token: 'variable', foreground: '08090a' },
      { token: 'operator', foreground: '62666d' },
      { token: 'delimiter', foreground: '62666d' },
      { token: 'regexp', foreground: 'f5a524' },
      { token: 'constant', foreground: '7170ff' },
      { token: 'attribute.name', foreground: '7170ff' },
      { token: 'attribute.value', foreground: '27a644' }
    ],
    colors: {
      'editor.background': '#f7f8f8',
      'editor.foreground': '#28282c',
      'editor.lineHighlightBackground': '#f3f4f5',
      'editorLineNumber.foreground': '#e6e6e6',
      'editorLineNumber.activeForeground': '#62666d',
      'editor.selectionBackground': 'rgba(94,106,210,0.25)',
      'editor.inactiveSelectionBackground': 'rgba(94,106,210,0.12)',
      'editorIndentGuide.background': '#e6e6e6',
      'editorIndentGuide.activeBackground': '#d0d6e0',
      'editorWidget.background': '#ffffff',
      'editorWidget.border': 'rgba(0,0,0,0.08)',
      'editorSuggestWidget.background': '#ffffff',
      'editorSuggestWidget.border': 'rgba(0,0,0,0.08)',
      'editorSuggestWidget.selectedBackground': 'rgba(94,106,210,0.15)',
      'editorCursor.foreground': '#7170ff',
      'editor.findMatchBackground': 'rgba(94,106,210,0.3)',
      'editor.findMatchHighlightBackground': 'rgba(94,106,210,0.15)',
      'scrollbarSlider.background': 'rgba(0,0,0,0.1)',
      'scrollbarSlider.hoverBackground': 'rgba(0,0,0,0.18)',
      'scrollbarSlider.activeBackground': 'rgba(0,0,0,0.25)',
      'editorGutter.background': '#f7f8f8',
      'editorOverviewRuler.border': 'rgba(0,0,0,0.05)'
    }
  })
}

export function currentMonacoTheme(): string {
  const t = document.documentElement.getAttribute('data-theme') || 'dark'
  return t === 'dark' ? 'linear-dark' : 'linear-light'
}

export function applyMonacoTheme(): void {
  defineThemes()
  monaco.editor.setTheme(currentMonacoTheme())
}

export { monaco }
