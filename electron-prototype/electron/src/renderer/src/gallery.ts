// gallery.ts：示例画廊与工具箱共用的卡片网格
// 卡片 = 图标 + 标题 + 描述 + 标签 + 质量分徽章 + 收藏星；hover 显现 [▶ 运行] [详情]
// 画廊全量示例按质量分降序（可切名称/最近运行），分批渲染防止 1300+ 卡片一次撑爆 DOM。
// 依赖：state、els（state.ts）、FilterEngine（filter-engine.ts）、favorites（favorites.ts）、app（runExample/openDetail）。

import { state, els } from './state'
import { escapeHtml, getToolIcon, qualityBadgeCls } from './utils'
import { CATEGORY_META } from './category-meta'
import * as FilterEngine from './filter-engine'
import { isFavorite, toggleFavorite } from './favorites'
import { applyAllFilters, persistViewPrefs } from './app'
import { openDetail, runFromCard } from './detail'

const PAGE_SIZE = 120

// 卡片（自原主题卡片模板泛化；类名统一 card-*）
const CARD_CLS =
  'card group bg-panel border border-line-subtle rounded-xl cursor-pointer transition-all duration-200 flex flex-col hover:border-line-strong hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)]'
const CARD_SELECTED_CLS = `${CARD_CLS} border-accent shadow-[0_0_0_2px_rgba(94,106,210,0.3)]`
const CARD_BTN_CLS =
  'card-btn flex-1 flex items-center justify-center gap-1.5 px-3 py-2 border border-line-subtle rounded-md text-[12px] font-[510] cursor-pointer transition-all duration-150 bg-panel text-ink-dim hover:border-line-strong hover:text-ink hover:bg-card'
const CARD_BTN_FAV_CLS =
  'card-btn card-btn-fav flex-none basis-[34px] flex items-center justify-center gap-1.5 px-3 py-2 border border-line-subtle rounded-md text-[12px] font-[510] cursor-pointer transition-all duration-150 bg-panel text-ink-mute hover:border-line-strong hover:text-ink hover:bg-card'

function cardIcon(ex): string {
  return ex.category === 'tools' ? getToolIcon(ex.name) : '🐍'
}

export function cardHtml(ex): string {
  const selected = ex.id === state.selectedId
  const faved = isFavorite(ex.id)
  const title = ex.title || ex.name.replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  const description = ex.description || '暂无描述'
  const tags = (ex.tags || []).slice(0, 2)
    .map((tag) => `<span class="card-tag inline-block text-[10px] px-2 py-0.5 bg-card rounded text-ink-dim font-mono font-[510]">${escapeHtml(tag)}</span>`)
    .join('')
  const catCls = (CATEGORY_META[ex.category] || {}).cls || ''
  const q = ex.quality_score ?? 0
  const exId = escapeHtml(ex.id)
  return `
    <div class="${selected ? CARD_SELECTED_CLS : CARD_CLS}" data-id="${exId}">
      <div class="card-header flex items-center gap-3 p-4 border-b border-line-subtle">
        <div class="card-icon w-10 h-10 rounded-[10px] flex items-center justify-center text-[20px] shrink-0 bg-card border border-line-subtle">${cardIcon(ex)}</div>
        <div class="card-info flex-1 min-w-0 flex flex-col gap-1">
          <div class="flex items-center gap-2 min-w-0">
            <span class="card-title text-[14px] font-[590] text-ink leading-[1.3] truncate capitalize">${escapeHtml(title)}</span>
            <span class="card-category inline-flex items-center px-1.5 py-px rounded-sm text-[9px] font-[590] uppercase tracking-[0.03em] shrink-0 ${catCls}">${escapeHtml(ex.category)}</span>
          </div>
          <div class="card-meta flex items-center gap-1.5">${tags}</div>
        </div>
        <span class="card-quality inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-[510] font-mono shrink-0 ${qualityBadgeCls(ex.quality_score)}" title="六维质量评分（0-100）">★ ${q}</span>
      </div>
      <div class="card-body flex-1 px-4 py-3">
        <p class="card-description text-[12px] text-ink-dim leading-[1.6] m-0 line-clamp-3">${escapeHtml(description)}</p>
      </div>
      <div class="card-actions flex gap-2 px-4 pt-3 pb-4 opacity-0 translate-y-1 transition-all duration-200 group-hover:opacity-100 group-hover:translate-y-0">
        <button class="${CARD_BTN_FAV_CLS}${faved ? ' text-[#e3a008] border-[#e3a008]' : ''}" data-action="fav" data-id="${exId}" title="${faved ? '取消收藏' : '收藏'}">${faved ? '★' : '☆'}</button>
        <button class="${CARD_BTN_CLS} bg-accent text-white border-accent font-[590] enabled:hover:bg-accent-hover enabled:hover:border-accent-hover" data-action="run" data-id="${exId}">▶ 运行</button>
        <button class="${CARD_BTN_CLS}" data-action="detail" data-id="${exId}">详情</button>
      </div>
    </div>`
}

/** 网格事件委托：卡片点击 → 详情；运行 → 直接运行；收藏星 → 切换 */
function bindGridEvents(host: HTMLElement): void {
  host.addEventListener('click', (e) => {
    const target = e.target as HTMLElement
    const actionBtn = target.closest('[data-action]') as HTMLElement | null
    if (actionBtn) {
      const id = actionBtn.dataset.id
      const action = actionBtn.dataset.action
      if (action === 'fav' && id) toggleFavorite(id)
      // 卡片运行：打开详情 → 必填参数缺失则引导填参，否则按表单默认值自动运行
      if (action === 'run' && id) runFromCard(id)
      if (action === 'detail' && id) openDetail(id)
      return
    }
    const card = target.closest('.card') as HTMLElement | null
    if (card && card.dataset.id) openDetail(card.dataset.id)
  })
}

function renderCardGrid(host: HTMLElement, items, opts?: { limit?: number }): void {
  const limit = opts?.limit
  const shown = typeof limit === 'number' ? items.slice(0, limit) : items
  if (shown.length === 0) {
    host.innerHTML =
      '<div class="card-empty col-span-full flex flex-col items-center justify-center px-6 py-12 text-ink-mute text-center"><div class="text-[48px] mb-3 opacity-50">🐍</div><div class="text-[16px] text-ink-dim">没有匹配的示例</div></div>'
    return
  }
  let html = shown.map(cardHtml).join('')
  if (typeof limit === 'number' && items.length > shown.length) {
    html += `<button id="gallery-load-more" class="col-span-full py-3 text-[12px] text-ink-mute border border-line-subtle rounded-lg bg-panel cursor-pointer hover:text-ink hover:border-line-strong transition-colors">加载更多（还有 ${items.length - shown.length} 个）</button>`
  }
  host.innerHTML = html
  const more = document.getElementById('gallery-load-more')
  if (more) {
    more.addEventListener('click', () => {
      state.galleryLimit += PAGE_SIZE
      renderGalleryGrid()
    })
  }
}

// ---------------------------------------------------------------------------
// 画廊
// ---------------------------------------------------------------------------
export function renderGalleryGrid(): void {
  if (!els.galleryGrid) return
  const sorted = FilterEngine.sortExamples(state.filtered, state.sortBy, {
    lastRunAt: state.lastRunIndex
  })
  renderCardGrid(els.galleryGrid, sorted, { limit: state.galleryLimit })
  if (state.activeView === 'gallery' && els.statusCount) {
    els.statusCount.textContent = `${state.filtered.length} / ${state.examples.length} 个示例`
  }
}

// ---------------------------------------------------------------------------
// 工具箱（category=tools 子集，共用筛选引擎与卡片）
// ---------------------------------------------------------------------------
// 由 app.ts 注入统一筛选上下文（favorites / runStatus / lastRunAt）
let _ctxProvider: () => any = () => ({})
export function setFilterContextProvider(fn: () => any): void {
  _ctxProvider = fn
}

function currentToolboxQuery() {
  return {
    category: 'tools',
    favOnly: state.favOnly,
    runStatus: state.activeRunStatus,
    tags: Array.from(state.activeTags as Set<string>),
    q: state.toolSearchQuery
  }
}

// 工具箱当前可见工具数的缓存：renderToolboxGrid 与 updateStatusCount 共用，
// 避免同一次筛选对 1300+ 示例做两遍相同的过滤
let _lastToolboxItems: any[] = []

export function renderToolboxGrid(): void {
  if (!els.toolboxGrid) return
  const items = FilterEngine.filterExamples(state.examples, currentToolboxQuery(), _ctxProvider())
  _lastToolboxItems = items
  renderCardGrid(els.toolboxGrid, items)
  if (state.activeView === 'toolbox' && els.statusCount) {
    els.statusCount.textContent = `${items.length} / ${toolboxTotal()} 个工具`
  }
}

function toolboxTotal(): number {
  return state.examples.filter((e) => e.category === 'tools').length
}

/** 工具箱当前可见工具数（复用最近一次渲染的过滤结果；未渲染过时现算一次） */
export function toolboxCount(): number {
  return _lastToolboxItems.length || FilterEngine.filterExamples(state.examples, currentToolboxQuery(), _ctxProvider()).length
}

// ---------------------------------------------------------------------------
// 初始化：搜索防抖 + 排序 + 网格事件
// ---------------------------------------------------------------------------
let _debounce: ReturnType<typeof setTimeout> | undefined

export function initGallery(): void {
  if (els.galleryGrid) bindGridEvents(els.galleryGrid)
  if (els.toolboxGrid) bindGridEvents(els.toolboxGrid)

  els.gallerySearch?.addEventListener('input', (e) => {
    state.searchQuery = (e.target as HTMLInputElement).value
    clearTimeout(_debounce)
    _debounce = setTimeout(() => applyAllFilters(), 150)
  })

  els.toolboxSearch?.addEventListener('input', (e) => {
    state.toolSearchQuery = (e.target as HTMLInputElement).value
    clearTimeout(_debounce)
    _debounce = setTimeout(() => applyAllFilters(), 150)
  })

  els.gallerySort?.addEventListener('change', (e) => {
    state.sortBy = (e.target as HTMLSelectElement).value as any
    persistViewPrefs()
    renderGalleryGrid()
  })
}
