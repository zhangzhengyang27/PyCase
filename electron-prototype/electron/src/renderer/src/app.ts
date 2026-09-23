// 渲染进程编排层（v0.6 画廊优先架构）。
// 职责：示例加载、统一筛选（filter-engine 组合查询）、三视图导航、
//       运行生命周期（run/stop/输出/图片按 runSink 路由）、明暗主题与快捷键。
// 卡片网格见 gallery.ts、详情页见 detail.ts、运行器见 runner.ts、筛选条见 facets.ts。

import { state, els, THEMES } from './state'
import { statusDotCls, OUTPUT_DOT_CLS } from './utils'
import * as FilterEngine from './filter-engine'
import { api } from './sidecar-client'
import { initMonaco } from './monaco-editor'
import { appendRunOutput, setSurfaceStatusDot, renderSurfaceImages } from './output'
import { initGallery, renderGalleryGrid, renderToolboxGrid, toolboxCount, setFilterContextProvider } from './gallery'
import { initDetail, saveExample, runFromDetail, detailRunStarted, detailRunFinished } from './detail'
import { initRunner, runnerRunStarted, runnerRunFinished, runnerRun } from './runner'

// 以下模块与 app.ts 存在循环依赖（它们在函数内部回调 app.ts 的编排函数），
// 采用顶部 import + 运行时调用（ESM 支持循环依赖，只要不在顶层直接使用）。
import { initHistoryPanel, loadHistory, recordHistory, updateHistoryBadge } from './history'
import { loadFavorites, updateFavChip, initFavorites } from './favorites'
import { renderFacets, initFacets } from './facets'
import { initAI, loadAISettings } from './ai'

// ---------------------------------------------------------------------------
// Sidecar 状态（唯一指示在底栏状态栏）
// ---------------------------------------------------------------------------
export function setSidecarStatus(ready: boolean): void {
  const st = ready ? 'ready' : 'error'
  const txt = ready ? '已连接' : '已断开'
  if (els.statusSidecarDot) els.statusSidecarDot.className = statusDotCls(st as 'ready' | 'error', 'sm')
  if (els.statusSidecarText) els.statusSidecarText.textContent = `sidecar ${txt}`
}

// ---------------------------------------------------------------------------
// 明暗主题
// ---------------------------------------------------------------------------
export function getCurrentTheme() {
  return document.documentElement.getAttribute('data-theme') || 'dark'
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('app-theme', theme)
  if (els.btnThemeToggle) {
    els.btnThemeToggle.textContent = theme === 'dark' ? '🌙' : '☀️'
    els.btnThemeToggle.title = theme === 'dark' ? '切换到亮色模式 (Cmd+J)' : '切换到暗黑模式 (Cmd+J)'
  }
  if (state.editor && state.monaco) {
    state.monaco.editor.setTheme(theme === 'dark' ? 'linear-dark' : 'linear-light')
  }
}

export function toggleTheme() {
  applyTheme(getCurrentTheme() === 'dark' ? 'light' : 'dark')
}

// 初始化主题（从 localStorage 读取，默认暗黑）
applyTheme(localStorage.getItem('app-theme') || 'dark')

api.on('status', (data) => {
  setSidecarStatus(data.ready)
  if (data.ready) {
    // sidecar 崩溃重启后正在进行的运行已随旧进程消失：复位运行态，
    // 否则 isRunning 永久为 true，所有运行入口被防重入 guard 禁用
    if (state.isRunning) {
      state.isRunning = false
      state.runSink = null
      state.currentRunId = null
      state.currentRunMeta = null
      runnerRunFinished()
      detailRunFinished()
      setSurfaceStatusDot('detail', OUTPUT_DOT_CLS.error)
      setSurfaceStatusDot('runner', OUTPUT_DOT_CLS.error)
      appendRunOutput('\n[系统] sidecar 已重启，本次运行中断\n', 'system')
      if (els.statusRun) els.statusRun.textContent = 'sidecar 已重启'
    }
    loadExamples()
  }
})

// ---------------------------------------------------------------------------
// 加载示例列表（一次性建立筛选所需的派生数据）
// ---------------------------------------------------------------------------
export async function loadExamples() {
  if (els.galleryGrid) {
    els.galleryGrid.innerHTML =
      '<div class="loading-placeholder col-span-full px-6 py-8 text-center text-ink-faint text-[12px]">加载示例中…（首次加载需物化所有示例，可能较慢）</div>'
  }
  if (els.toolboxGrid) {
    els.toolboxGrid.innerHTML =
      '<div class="loading-placeholder col-span-full px-6 py-8 text-center text-ink-faint text-[12px]">加载工具中…</div>'
  }
  try {
    const result: any = await api.listExamples()
    state.examples = result.examples || []
    // 一次性建立筛选派生数据（每次按键的全量扫描都依赖它们，避免热路径重复解析）：
    // _importTags：import 自动标签；_codeLower：全文搜索用小写代码；_tagsAll：合并标签
    state.examples.forEach((ex) => {
      ex._importTags = FilterEngine.extractImportTags(ex.code)
      ex._codeLower = (ex.code || '').toLowerCase()
      ex._tagsAll = FilterEngine.allTagsOf(ex)
    })
    // 运行历史可能先于列表加载完成，这里统一补建索引
    rebuildIndexes()
    applyAllFilters()
  } catch (err) {
    if (els.galleryGrid) {
      els.galleryGrid.innerHTML = ''
      const div = document.createElement('div')
      div.className = 'empty-placeholder col-span-full px-6 py-8 text-center text-ink-faint text-[12px]'
      div.textContent = `加载失败: ${(err as any).message}`
      els.galleryGrid.appendChild(div)
    }
    if (els.toolboxGrid) {
      els.toolboxGrid.innerHTML = ''
      const div = document.createElement('div')
      div.className = 'empty-placeholder col-span-full px-6 py-8 text-center text-ink-faint text-[12px]'
      div.textContent = `加载失败: ${(err as any).message}`
      els.toolboxGrid.appendChild(div)
    }
    console.error('加载示例失败:', err)
  }
}

// ---------------------------------------------------------------------------
// 筛选与渲染（多维条件统一交给 filter-engine，UI 层不再写 elif 分支）
// ---------------------------------------------------------------------------
// 主题谓词表（THEMES 配置 → filter-engine ctx 注入，模块级构建一次）
const THEME_MATCHERS = Object.fromEntries(THEMES.map((t) => [t.key, t.filter]))

// 由全局 state 组装当前查询（收藏 × 运行状态 × 主题 × 质量分 × 标签 × 全文）
export function currentFilterQuery(overrides?: any) {
  return Object.assign(
    {
      favOnly: state.favOnly,
      runStatus: state.activeRunStatus,
      theme: state.activeTheme,
      minQuality: state.minQuality,
      tags: Array.from(state.activeTags),
      q: state.searchQuery
    },
    overrides || {}
  )
}

export function filterContext() {
  return {
    favorites: state.favorites,
    runStatus: state.runStatusIndex,
    themeMatchers: THEME_MATCHERS,
    lastRunAt: state.lastRunIndex
  }
}

export function applyFilters() {
  state.filtered = FilterEngine.filterExamples(state.examples, currentFilterQuery(), filterContext())
}

// ---------------------------------------------------------------------------
// 视图偏好持久化（userData/viewPrefs：排序 / 主题维度 / 质量分阈值）
// 只持久化跨会话有意义的偏好；收藏开关与运行状态等会话性条件不落盘
// ---------------------------------------------------------------------------
export async function loadViewPrefs(): Promise<void> {
  try {
    const prefs = await api.storeGet('viewPrefs')
    if (prefs && typeof prefs === 'object') {
      if (['quality_desc', 'name', 'last_run'].includes(prefs.sortBy)) state.sortBy = prefs.sortBy
      // activeTheme 必须是 THEMES 的合法 key：脏数据会让 filter-engine
      // 找不到匹配器而静默放行全部示例
      if (typeof prefs.activeTheme === 'string' && THEMES.some((t) => t.key === prefs.activeTheme)) {
        state.activeTheme = prefs.activeTheme
      }
      if (typeof prefs.minQuality === 'number' && prefs.minQuality >= 0) state.minQuality = prefs.minQuality
    }
  } catch (err) {
    console.error('加载视图偏好失败:', err)
  }
  // 同步排序下拉显示
  if (els.gallerySort) (els.gallerySort as HTMLSelectElement).value = state.sortBy
}

export function persistViewPrefs(): void {
  api
    .storeSet('viewPrefs', { sortBy: state.sortBy, activeTheme: state.activeTheme, minQuality: state.minQuality })
    .catch(() => {})
}

// 任意筛选条件变化后的统一重筛入口（画廊 / 工具箱 / facet 计数一起刷新）
export function applyAllFilters() {
  applyFilters()
  renderGalleryGrid()
  renderToolboxGrid()
  renderFacets()
  updateStatusCount()
}

function updateStatusCount() {
  if (!els.statusCount) return
  if (state.activeView === 'toolbox') {
    // 工具箱计数用工具箱自身查询（不含画廊专属的主题/质量维度）
    els.statusCount.textContent = `${toolboxCount()} / ${state.examples.filter((e) => e.category === 'tools').length} 个工具`
  } else {
    els.statusCount.textContent = `${state.filtered.length} / ${state.examples.length} 个示例`
  }
}

// 运行历史变化后重建 运行状态/最近运行 索引并重筛
export function rebuildIndexes() {
  state.runStatusIndex = FilterEngine.buildRunStatusIndex(state.runHistory)
  state.lastRunIndex = FilterEngine.buildLastRunIndex(state.runHistory)
}

export function rebuildRunStatusIndex() {
  rebuildIndexes()
  applyAllFilters()
}

// ---------------------------------------------------------------------------
// 运行生命周期（输出/图片/状态按 runSink 路由到唯一可见面板）
// ---------------------------------------------------------------------------
export async function runExample(opts?: { id?: string; args?: string[]; sink?: 'detail' | 'runner' }) {
  const id = opts?.id || state.selectedId
  if (!id || state.isRunning) return
  const ex = state.examples.find((e) => e.id === id)
  if (!ex) return

  const sink = opts?.sink || 'detail'
  state.isRunning = true
  state.runSink = sink

  // 清空目标面板并进入运行态（每个面板自带清空与状态点逻辑）
  if (sink === 'runner') runnerRunStarted()
  else detailRunStarted()
  appendRunOutput(`▶ 运行: ${ex.name}\n`, 'system')

  const runArgs = opts?.args || []
  if (runArgs.length > 0) {
    appendRunOutput(`  参数: ${runArgs.join(' ')}\n`, 'system')
  }

  try {
    state.currentRunMeta = { id, name: ex.name, args: runArgs, startedAt: Date.now() }
    const params: any = { id, timeout: 30 }
    if (runArgs.length > 0) params.args = runArgs
    const result = await api.runExample(params)
    state.currentRunId = result.run_id
    appendRunOutput(`  run_id: ${result.run_id}\n`, 'system')
  } catch (err) {
    appendRunOutput(`[错误] 启动失败: ${(err as any).message}\n`, 'error')
    state.isRunning = false
    state.runSink = null
    state.currentRunMeta = null // 正常路径在 runFinished 清理，失败路径同样不能悬挂
    if (sink === 'runner') runnerRunFinished()
    else detailRunFinished()
    setSurfaceStatusDot(sink, OUTPUT_DOT_CLS.error)
    if (els.statusRun) els.statusRun.textContent = '启动失败'
  }
}

export async function stopRun() {
  if (!state.currentRunId) return
  try {
    await api.stopRun(state.currentRunId)
    appendRunOutput('\n[系统] 已发送停止指令\n', 'system')
  } catch (err) {
    appendRunOutput(`[错误] 停止失败: ${(err as any).message}\n`, 'error')
  }
}

api.on('runOutput', (data) => {
  if (data.run_id !== state.currentRunId) return
  const text = data.text || ''
  const isSystem = text.startsWith('[系统]') || text.startsWith('[错误]')
  appendRunOutput(text, isSystem ? 'system' : '')
})

api.on('runImages', (data) => {
  if (data.run_id !== state.currentRunId) return
  // run_images 先于 run_finished 到达，runSink 仍然有效
  renderSurfaceImages(state.runSink || 'detail', data.images || [])
})

api.on('runFinished', (data) => {
  if (data.run_id !== state.currentRunId) return
  const exitCode = data.exit_code
  const sink = state.runSink || 'detail'
  if (exitCode === 0) {
    appendRunOutput(`✓ 运行成功 (exit code: 0)\n`, 'success')
    setSurfaceStatusDot(sink, OUTPUT_DOT_CLS.success)
    if (els.statusRun) els.statusRun.textContent = '运行成功'
  } else {
    appendRunOutput(`✗ 运行失败 (exit code: ${exitCode})\n`, 'error')
    setSurfaceStatusDot(sink, OUTPUT_DOT_CLS.error)
    if (els.statusRun) els.statusRun.textContent = '运行失败'
  }
  state.isRunning = false
  state.runSink = null
  // 记录运行历史（成功/失败均记录）并刷新运行状态索引
  recordHistory(state.currentRunMeta, exitCode)
  state.currentRunMeta = null
  state.currentRunId = null
  if (sink === 'runner') runnerRunFinished()
  else detailRunFinished()
})

// 主题示例运行结果图片下载（保存对话框）
export async function downloadResultImage(url, name) {
  try {
    const res = await api.downloadResultImage(url, name)
    if (!res || res.canceled) return
    if (res.error) {
      window.alert(`下载失败：${res.error}`)
      return
    }
  } catch (err) {
    window.alert(`下载失败：${(err as any).message}`)
  }
}

// ---------------------------------------------------------------------------
// 视图导航（gallery / toolbox / runner；详情页打开时跳转即关闭详情）
// ---------------------------------------------------------------------------
export function switchView(viewKey) {
  // 详情页编辑未保存时导航离开会静默丢弃修改，需确认
  if (state.activeView !== viewKey && state.isDirty && !window.confirm('当前示例有未保存的修改，丢弃并切换视图？')) {
    return
  }
  state.activeView = viewKey
  const views = { gallery: els.viewGallery, toolbox: els.viewToolbox, runner: els.viewRunner }
  for (const [key, el] of Object.entries(views)) {
    if (el) (el as HTMLElement).style.display = key === viewKey ? '' : 'none'
  }
  if (els.detailPage) els.detailPage.style.display = 'none'
  document.querySelectorAll('.nav-segment').forEach((t) => t.classList.toggle('active', (t as HTMLElement).dataset.view === viewKey))
  updateStatusCount()
}

// 静态导航按钮（画廊 / 工具箱 / 运行器）
els.navSegments.forEach((tab) => {
  tab.addEventListener('click', () => switchView((tab as HTMLElement).dataset.view))
})

// 事件绑定
els.btnRefresh?.addEventListener('click', loadExamples)
els.btnThemeToggle?.addEventListener('click', toggleTheme)

// 键盘快捷键
document.addEventListener('keydown', (e) => {
  if (!(e.ctrlKey || e.metaKey)) return
  if (e.key === 's') {
    e.preventDefault()
    if (state.isDirty) saveExample()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (state.isRunning) return
    if (state.activeView === 'runner') runnerRun()
    else runFromDetail()
  } else if (e.key === '.') {
    e.preventDefault()
    if (state.isRunning) stopRun()
  } else if (e.key === 'j') {
    e.preventDefault()
    toggleTheme()
  }
})

// ---------------------------------------------------------------------------
// 启动：初始化各模块 → Monaco → 连接 sidecar
// ---------------------------------------------------------------------------
export async function bootstrap(): Promise<void> {
  // 1) 各视图与弹窗初始化
  initFacets()
  initGallery()
  initDetail()
  initRunner()
  initHistoryPanel()
  // 2) 收藏、历史与视图偏好的数据加载（完成后经 applyAllFilters 刷新状态索引）
  initFavorites()
  loadFavorites()
  loadHistory()
  await loadViewPrefs()
  // 3) AI 代码解释（DeepSeek）
  initAI()
  loadAISettings()

  // 统一筛选上下文注入（画廊/工具箱共用）
  setFilterContextProvider(filterContext)
  updateHistoryBadge()

  try {
    await initMonaco()
    console.debug('[Monaco] 编辑器初始化完成')
  } catch (err) {
    console.error('[Monaco] 初始化失败:', err)
    if (els.monacoContainer) {
      els.monacoContainer.textContent = ''
      const div = document.createElement('div')
      div.style.cssText = 'padding:20px;color:#e5484d;font-family:monospace;'
      div.textContent = `Monaco 初始化失败: ${(err as Error).message}`
      els.monacoContainer.appendChild(div)
    }
  }

  // 尝试 ping sidecar
  api
    .ping()
    .then(() => {
      setSidecarStatus(true)
      loadExamples()
    })
    .catch(() => {
      // 等待 onStatus 事件
    })
}
