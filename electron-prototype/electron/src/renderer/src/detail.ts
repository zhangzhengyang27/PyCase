// detail.ts：示例详情页（单例，画廊/工具箱共用）
// 结构：头部（返回/标题/标签/质量分/收藏/AI/保存/停止/运行）
//       + 参数表单（argparse，可折叠）+ Monaco 源码区
//       + 下半区三标签（终端输出 / 资源 / 运行历史）
// 职责：打开与关闭、示例装载、编辑脏标记与保存回写、参数联动、标签页切换、内嵌历史。
// 依赖：state、els（state.ts）、api（sidecar-client.ts）、args-form/assets/output/favorites/app。

import { state, els } from './state'
import { api } from './sidecar-client'
import { escapeHtml, qualityBadgeCls, OUTPUT_DOT_CLS } from './utils'
import { CATEGORY_META } from './category-meta'
import { appendDetailOutput, clearSurfaceOutput, clearSurfaceImages, setSurfaceStatusDot } from './output'
import { updateActionBarFav } from './favorites'
import { loadAndRenderArgs, invalidateArgsCache, requiredArgsMissing, collectArgsFromForm, applyArgsToForm } from './args-form'
import { refreshDetailAssets, uploadDetailAssets } from './assets'
import { runExample, stopRun } from './app'

// JS 整体替换 className 的标签按钮：完整工具类串（utils.ts 约定）
const DETAIL_TAB_CLS =
  'detail-tab px-3 py-1 rounded-md text-[11px] font-[510] font-sans cursor-pointer border-0 bg-transparent text-ink-mute hover:text-ink transition-colors duration-[120ms]'
const DETAIL_TAB_ACTIVE_CLS = `${DETAIL_TAB_CLS} bg-page text-ink`
const HISTORY_BADGE_OK_CLS =
  'shrink-0 text-[11px] font-[590] px-2 py-0.5 rounded-full text-[#1a7f37] bg-[rgba(63,185,80,0.14)]'
const HISTORY_BADGE_FAIL_CLS =
  'shrink-0 text-[11px] font-[590] px-2 py-0.5 rounded-full text-[#cf222e] bg-[rgba(248,81,73,0.14)]'

// ---------------------------------------------------------------------------
// 打开 / 关闭
// ---------------------------------------------------------------------------
/** 打开详情页并装载：返回参数解析 Promise（卡片「运行」据此决定自动运行或引导填参） */
export function openDetail(id: string, fromView?): Promise<any[]> {
  const ex = state.examples.find((e) => e.id === id)
  if (!ex || !els.detailPage) return Promise.resolve([])

  // 未保存的编辑不得静默丢弃：切换到不同示例前需要确认
  if (state.selectedId && state.selectedId !== id && state.isDirty && !window.confirm('当前示例有未保存的修改，丢弃并继续？')) {
    return Promise.resolve([])
  }

  // 与当前选中不同的示例：丢弃参数解析缓存
  if (state.selectedId !== id) invalidateArgsCache()
  state.selectedId = id
  state.detailFrom = fromView && fromView !== 'runner' ? fromView : state.activeView === 'toolbox' ? 'toolbox' : 'gallery'

  // 头部信息
  if (els.detailTitle) els.detailTitle.textContent = ex.title || ex.name.replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  if (els.detailIcon) els.detailIcon.textContent = ex.category === 'tools' ? '🧰' : '🐍'
  if (els.detailCategory) {
    const meta = CATEGORY_META[ex.category]
    if (meta) {
      els.detailCategory.textContent = ex.category
      els.detailCategory.className = `inline-flex items-center px-2 py-0.5 rounded-sm text-[9px] font-[590] uppercase tracking-[0.03em] shrink-0 ${meta.cls}`
      els.detailCategory.style.display = ''
    } else {
      els.detailCategory.style.display = 'none'
    }
  }
  if (els.detailTags) {
    els.detailTags.innerHTML = (ex.tags || [])
      .slice(0, 6)
      .map((tag) => `<span class="inline-block text-[10px] px-2 py-0.5 bg-card rounded text-ink-dim font-mono font-[510]">${escapeHtml(tag)}</span>`)
      .join('')
  }
  if (els.detailQuality) {
    els.detailQuality.className = `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-[510] font-mono shrink-0 ${qualityBadgeCls(ex.quality_score)}`
    els.detailQuality.textContent = `★ ${ex.quality_score ?? 0}`
  }

  // 装载源码
  state.originalCode = ex.code || ''
  state.isDirty = false
  if (state.editor) {
    state.editor.setValue(state.originalCode)
    updateTitleDirty()
  }
  if (els.btnSave) els.btnSave.disabled = true

  // 运行按钮可用（runExample 内部有 isRunning 防重入）
  if (els.btnRun) els.btnRun.disabled = false
  if (els.btnStop) els.btnStop.disabled = !state.isRunning
  updateActionBarFav()

  // 切换显示：隐藏来源视图，显示详情页；默认停在「终端输出」标签
  hideCurrentView()
  els.detailPage.style.display = ''
  switchDetailTab('output')

  // 参数表单 / 资源 / 内嵌历史
  const argsPromise = loadAndRenderArgs(id)
  refreshDetailAssets(id)
  renderDetailHistory()

  // Monaco 在隐藏容器中不感知尺寸变化，显示后重排
  setTimeout(() => {
    if (state.editor) state.editor.layout()
  }, 50)
  return argsPromise
}

function hideCurrentView(): void {
  const map = { gallery: els.viewGallery, toolbox: els.viewToolbox, runner: els.viewRunner }
  const active = map[state.detailFrom] || map.gallery
  if (active) active.style.display = 'none'
}

function showOriginView(): void {
  const map = { gallery: els.viewGallery, toolbox: els.viewToolbox, runner: els.viewRunner }
  const active = map[state.detailFrom] || map.gallery
  if (active) active.style.display = ''
}

export function closeDetail(): void {
  if (!els.detailPage) return
  // 返回画廊前确认：编辑内容会被 Monaco 重载覆盖，静默丢弃不可接受
  if (state.isDirty && !window.confirm('当前示例有未保存的修改，丢弃并返回？')) return
  els.detailPage.style.display = 'none'
  showOriginView()
  setTimeout(() => {
    if (state.editor) state.editor.layout()
  }, 50)
}

// ---------------------------------------------------------------------------
// 下半区标签页（终端输出 / 资源 / 历史）
// ---------------------------------------------------------------------------
function switchDetailTab(tab: 'output' | 'assets' | 'history'): void {
  const containers = { output: els.detailTabOutput, assets: els.detailTabAssets, history: els.detailTabHistory }
  const btns = { output: els.detailTabBtnOutput, assets: els.detailTabBtnAssets, history: els.detailTabBtnHistory }
  for (const key of Object.keys(containers) as Array<'output' | 'assets' | 'history'>) {
    if (containers[key]) (containers[key] as HTMLElement).style.display = key === tab ? '' : 'none'
    if (btns[key]) (btns[key] as HTMLElement).className = key === tab ? DETAIL_TAB_ACTIVE_CLS : DETAIL_TAB_CLS
  }
}

// ---------------------------------------------------------------------------
// 运行（收集参数表单 → runExample；输出汇固定 detail）
// ---------------------------------------------------------------------------
export function runFromDetail(): void {
  if (state.isRunning || !state.selectedId) return
  const args = collectArgsFromForm()
  runExample({ id: state.selectedId, args, sink: 'detail' })
}

/** 卡片「▶ 运行」入口：打开详情后，必填参数缺失则留在表单引导填写，否则按当前表单值自动运行 */
export function runFromCard(id: string): void {
  void openDetail(id).then((args) => {
    // openDetail 异步等待期间用户可能已点开别的示例：此时运行的就是那个示例了
    if (state.selectedId !== id) return
    if (requiredArgsMissing(args)) return
    runFromDetail()
  })
}

// ---------------------------------------------------------------------------
// 标题脏标记与保存回写
// ---------------------------------------------------------------------------
export function updateTitleDirty(): void {
  if (!state.selectedId || !els.detailTitle) return
  const ex = state.examples.find((e) => e.id === state.selectedId)
  if (!ex) return
  els.detailTitle.textContent = (ex.title || ex.name.replace(/\.py$/i, '').replace(/[-_]/g, ' ')) + (state.isDirty ? ' ●' : '')
}

export async function saveExample(): Promise<void> {
  const id = state.selectedId
  if (!id || !state.isDirty || !state.editor) return

  const newCode = state.editor.getValue()
  if (els.btnSave) {
    els.btnSave.disabled = true
    els.btnSave.textContent = '保存中…'
  }

  try {
    const result = await api.saveExample(id, newCode)
    // 保存期间用户可能已切换示例：状态只能写回保存时那个示例，
    // 否则新示例的 code/isDirty/originalCode 会被覆盖（丢编辑、错标签）
    if (state.selectedId !== id) return
    state.originalCode = newCode
    state.isDirty = false
    updateTitleDirty()
    appendDetailOutput(`[系统] 已保存: ${result.json_file || result.path}\n`, 'system')
    // 同步示例列表中的代码并重解析参数（argparse 定义可能变化）
    const ex = state.examples.find((e) => e.id === id)
    if (ex) {
      ex.code = newCode
      import('./filter-engine').then(({ extractImportTags, allTagsOf }) => {
        ex._importTags = extractImportTags(newCode)
        // 同步重建筛选缓存，否则全文搜索/标签 facet 还是旧代码的内容
        ex._codeLower = newCode.toLowerCase()
        ex._tagsAll = allTagsOf(ex)
      })
    }
    invalidateArgsCache()
    loadAndRenderArgs(id)
  } catch (err) {
    appendDetailOutput(`[错误] 保存失败: ${(err as any).message}\n`, 'error')
    if (els.btnSave) els.btnSave.disabled = false
  } finally {
    if (els.btnSave) els.btnSave.textContent = '💾 保存'
  }
}

// ---------------------------------------------------------------------------
// 内嵌运行历史（当前示例，最近 20 条，可重跑）
// ---------------------------------------------------------------------------
function formatTime(iso: string): string {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

export function renderDetailHistory(): void {
  if (!els.detailTabHistory) return
  const id = state.selectedId
  const rows = id ? state.runHistory.filter((h) => h.id === id).slice(0, 20) : []
  if (els.detailHistoryCount) {
    els.detailHistoryCount.textContent = rows.length ? `(${rows.length})` : ''
  }
  if (!id) return
  if (rows.length === 0) {
    els.detailTabHistory.innerHTML =
      '<div class="text-ink-mute text-[13px] px-3 py-2">该示例还没有运行记录</div>'
    return
  }
  els.detailTabHistory.innerHTML = rows
    .map((h, i) => {
      const badge = h.ok
        ? `<span class="${HISTORY_BADGE_OK_CLS}">成功</span>`
        : `<span class="${HISTORY_BADGE_FAIL_CLS}">失败 ${h.exit_code}</span>`
      const args = h.args && h.args.length ? ` · 参数 ${escapeHtml(h.args.join(' '))}` : ''
      return `
        <div class="flex items-center justify-between gap-3 px-3 py-1.5 border-b border-line-subtle hover:bg-[rgba(127,127,127,0.06)]">
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            ${badge}
            <span class="text-[11.5px] text-ink-dim truncate">${formatTime(h.ts)} · ${formatDuration(h.duration_ms)}${args}</span>
          </div>
          <button class="history-rerun btn btn-ghost inline-flex items-center px-2 py-0.5 border border-line-subtle rounded-md bg-transparent text-ink-dim text-[11px] font-[510] cursor-pointer hover:bg-hover hover:text-ink shrink-0" data-idx="${i}">重跑</button>
        </div>`
    })
    .join('')
  els.detailTabHistory.querySelectorAll('.history-rerun').forEach((btn) => {
    btn.addEventListener('click', () => {
      const entry = rows[Number((btn as HTMLElement).dataset.idx)]
      if (!entry || state.isRunning) return
      // 回填记录参数到表单再运行，保证表单与实际执行一致
      applyArgsToForm(entry.args || [])
      runFromDetail()
    })
  })
}

/** 运行历史变化后刷新内嵌列表（history.ts 回调） */
export function refreshDetailHistory(): void {
  if (!els || !els.detailPage || els.detailPage.style.display === 'none') return
  renderDetailHistory()
}

// ---------------------------------------------------------------------------
// 运行开始 / 结束时详情页面板状态（由 app.ts 调用）
// ---------------------------------------------------------------------------
export function detailRunStarted(): void {
  if (els.btnStop) els.btnStop.disabled = false
  if (els.btnRun) els.btnRun.disabled = true
  setSurfaceStatusDot('detail', OUTPUT_DOT_CLS.running)
  clearSurfaceOutput('detail')
  clearSurfaceImages('detail')
  // 运行时切回输出标签，保证实时输出可见
  if (els.detailPage && els.detailPage.style.display !== 'none') switchDetailTab('output')
  if (els.statusRun) els.statusRun.textContent = '运行中…'
}

export function detailRunFinished(): void {
  if (els.btnStop) els.btnStop.disabled = true
  if (els.btnRun) els.btnRun.disabled = !state.selectedId
}

// ---------------------------------------------------------------------------
// 初始化：头部按钮 + 标签页 + 参数折叠 + 资源上传 + 输出区
// ---------------------------------------------------------------------------
export function initDetail(): void {
  els.detailBack?.addEventListener('click', closeDetail)
  els.btnSave?.addEventListener('click', saveExample)
  els.btnRun?.addEventListener('click', runFromDetail)
  els.btnStop?.addEventListener('click', stopRun)

  // 标签页切换
  const tabBtns: Array<['output' | 'assets' | 'history', HTMLElement | null]> = [
    ['output', els.detailTabBtnOutput],
    ['assets', els.detailTabBtnAssets],
    ['history', els.detailTabBtnHistory]
  ]
  tabBtns.forEach(([key, btn]) => {
    btn?.addEventListener('click', () => switchDetailTab(key))
  })

  // 参数面板折叠/展开
  els.argsHeader?.addEventListener('click', () => {
    els.argsPanel?.classList.toggle('collapsed')
  })

  // 资源上传
  els.detailAssetsUpload?.addEventListener('click', () => {
    ;(els.detailAssetsFile as HTMLElement | null)?.click()
  })
  els.detailAssetsFile?.addEventListener('change', (e) => {
    const id = state.selectedId
    const files = Array.from((e.target as HTMLInputElement).files || [])
    ;(e.target as HTMLInputElement).value = ''
    if (id && files.length) uploadDetailAssets(id, files)
  })

  // 输出清空
  els.btnClearOutput?.addEventListener('click', () => {
    clearSurfaceOutput('detail')
    clearSurfaceImages('detail')
    setSurfaceStatusDot('detail', OUTPUT_DOT_CLS.idle)
    if (els.statusRun) els.statusRun.textContent = '就绪'
  })
}
