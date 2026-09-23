// monaco-editor.ts：Monaco Editor 初始化与封装（vite ESM + worker 模式，按需导入）
// 编辑器实例驻留详情页源码区；依赖：state（state.ts）、updateTitleDirty（detail.ts，循环引用仅运行时调用）

// 按需导入：只导入编辑器核心 + Python 语言，不导入所有语言（减小体积）
import * as monaco from 'monaco-editor/editor/editor.api'
import 'monaco-editor/languages/definitions/python/register'
import editorWorker from 'monaco-editor/editor/editor.worker?worker'
import { state, els } from './state'
import { updateTitleDirty } from './detail'

// 配置 Monaco worker（仅需 editor worker，Python 语言由 editor worker 处理基础语法）
self.MonacoEnvironment = {
  getWorker(_workerId: string, _label: string) {
    return new editorWorker()
  }
}

// ---------------------------------------------------------------------------
// Monaco Editor 初始化（ESM 模式，同步创建）
// ---------------------------------------------------------------------------
export function initMonaco(): Promise<unknown> {
  return new Promise((resolve, reject) => {
    try {
      state.monaco = monaco
      state.editor = monaco.editor.create(els.monacoContainer!, {
        value: '# 在画廊或工具箱中选择示例查看与编辑代码\n',
        language: 'python',
        theme: 'vs-dark',
        fontSize: 13,
        fontLigatures: true,
        minimap: { enabled: true, renderCharacters: false },
        scrollBeyondLastLine: false,
        smoothScrolling: true,
        cursorBlinking: 'smooth',
        renderWhitespace: 'selection',
        tabSize: 4,
        insertSpaces: true,
        automaticLayout: true,
        readOnly: false,
        wordWrap: 'on',
        padding: { top: 8, bottom: 8 }
      })

      // 监听代码变更，设置 dirty 状态
      state.editor.onDidChangeModelContent(() => {
        if (state.selectedId) {
          const currentCode = state.editor.getValue()
          state.isDirty = currentCode !== state.originalCode
          updateTitleDirty()
          if (els.btnSave) els.btnSave.disabled = !state.isDirty
        }
      })

      // Helper: read CSS variable at runtime (no hardcoded colors)
      const cssVar = (name: string) =>
        getComputedStyle(document.documentElement).getPropertyValue(name).trim()
      const hex = (name: string) => cssVar(name).replace('#', '')
      const rgba = (name: string, alpha: number) => {
        const h = cssVar(name).replace('#', '')
        const r = parseInt(h.slice(0, 2), 16)
        const g = parseInt(h.slice(2, 4), 16)
        const b = parseInt(h.slice(4, 6), 16)
        return `rgba(${r},${g},${b},${alpha})`
      }

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

      // 设置初始主题（与 CSS 主题同步）
      const initialTheme = document.documentElement.getAttribute('data-theme') || 'dark'
      monaco.editor.setTheme(initialTheme === 'dark' ? 'linear-dark' : 'linear-light')

      // 窗口大小变化时重新布局
      window.addEventListener('resize', () => {
        if (state.editor) state.editor.layout()
      })

      resolve(state.editor)
    } catch (e) {
      reject(e)
    }
  })
}
