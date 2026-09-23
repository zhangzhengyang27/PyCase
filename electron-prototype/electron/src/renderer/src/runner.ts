// runner.ts：代码运行器视图（最基础的运行入口）
// 左：示例快速搜索（名称匹配 Top 8）+ 只读源码预览；右：单行参数 + 运行/停止 + 终端输出 + 结果图。
// 明确不做：编辑（去详情页）、参数表单、资源、AI。
// 依赖：state、els（state.ts）、escapeHtml/splitArgs（utils.ts）、output（output.ts）、app（runExample/stopRun）。

import { state, els } from './state'
import { escapeHtml, splitArgs, OUTPUT_DOT_CLS } from './utils'
import { appendRunOutput, clearSurfaceOutput, clearSurfaceImages, setSurfaceStatusDot } from './output'
import { runExample, stopRun } from './app'

function selectedExample() {
  return state.examples.find((e) => e.id === state.runnerSelectedId) || null
}

// ---------------------------------------------------------------------------
// 快速搜索
// ---------------------------------------------------------------------------
function renderResults(list: string): void {
  if (!els.runnerResults) return
  els.runnerResults.innerHTML = list
  els.runnerResults.style.display = list ? '' : 'none'
}

function onSearchInput(query: string): void {
  const q = query.trim().toLowerCase()
  if (!q) {
    renderResults('')
    return
  }
  const hits = state.examples
    .filter((e) => e.name.toLowerCase().includes(q))
    .slice(0, 8)
  if (hits.length === 0) {
    renderResults('<div class="px-3 py-2 text-[12px] text-ink-faint">无匹配示例</div>')
    return
  }
  renderResults(
    hits
      .map(
        (e) =>
          `<button class="runner-result-item w-full flex items-center gap-2 px-3 py-1.5 text-left border-0 bg-transparent cursor-pointer text-[12px] text-ink-dim hover:bg-hover hover:text-ink" data-id="${e.id}">
            <span class="shrink-0">🐍</span><span class="truncate">${escapeHtml(e.name)}</span>
            <span class="ml-auto shrink-0 text-[10px] text-ink-faint font-mono">${e.quality_score ?? 0}</span>
          </button>`
      )
      .join('')
  )
}

function selectRunnerExample(id: string): void {
  const ex = state.examples.find((e) => e.id === id)
  if (!ex) return
  state.runnerSelectedId = id
  if (els.runnerTitle) els.runnerTitle.textContent = ex.name
  if (els.runnerCode) els.runnerCode.textContent = ex.code || ''
  if (els.runnerRun) els.runnerRun.disabled = false
  renderResults('')
  if (els.runnerSearch) els.runnerSearch.value = ''
}

// ---------------------------------------------------------------------------
// 运行
// ---------------------------------------------------------------------------
export function runnerRun(): void {
  const ex = selectedExample()
  if (!ex || state.isRunning) return
  const args = splitArgs((els.runnerArgs as HTMLInputElement)?.value || '')
  runExample({ id: ex.id, args, sink: 'runner' })
}

function clearRunnerOutput(): void {
  clearSurfaceOutput('runner')
  clearSurfaceImages('runner')
  setSurfaceStatusDot('runner', OUTPUT_DOT_CLS.idle)
  if (els.statusRun) els.statusRun.textContent = '就绪'
}

// ---------------------------------------------------------------------------
// 初始化
// ---------------------------------------------------------------------------
export function initRunner(): void {
  els.runnerSearch?.addEventListener('input', (e) => onSearchInput((e.target as HTMLInputElement).value))
  // 失焦收起候选（mousedown 先于 blur 触发，保证点击选中）
  els.runnerSearch?.addEventListener('blur', () => setTimeout(() => renderResults(''), 120))

  els.runnerResults?.addEventListener('mousedown', (e) => {
    const btn = (e.target as HTMLElement).closest('.runner-result-item') as HTMLElement | null
    if (btn && btn.dataset.id) {
      e.preventDefault()
      selectRunnerExample(btn.dataset.id)
    }
  })

  els.runnerRun?.addEventListener('click', runnerRun)
  els.runnerStop?.addEventListener('click', stopRun)
  els.runnerClear?.addEventListener('click', clearRunnerOutput)
  // 参数框内 Enter 直接运行
  els.runnerArgs?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      runnerRun()
    }
  })
}

/** 运行开始时由 app.ts 调用：切换运行器面板状态 */
export function runnerRunStarted(): void {
  if (els.runnerStop) els.runnerStop.disabled = false
  if (els.runnerRun) els.runnerRun.disabled = true
  setSurfaceStatusDot('runner', OUTPUT_DOT_CLS.running)
  clearSurfaceOutput('runner')
  clearSurfaceImages('runner')
  if (els.statusRun) els.statusRun.textContent = '运行中…'
}

/** 运行结束时由 app.ts 调用：恢复运行器按钮 */
export function runnerRunFinished(): void {
  if (els.runnerStop) els.runnerStop.disabled = true
  if (els.runnerRun) els.runnerRun.disabled = !state.runnerSelectedId
}
