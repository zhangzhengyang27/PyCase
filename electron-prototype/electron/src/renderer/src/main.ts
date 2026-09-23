// 渲染层入口（vite + TS + tailwind，全 ESM）

import './style.css'

// 全局错误捕获
window.addEventListener('error', (e) => {
  console.error('[renderer] Uncaught error:', e.error || e.message)
})
window.addEventListener('unhandledrejection', (e) => {
  console.error('[renderer] Unhandled rejection:', e.reason)
})

// 核心模块
import { state, els, THEMES } from './state'
import * as utils from './utils'
import * as FilterEngine from './filter-engine'
import { api } from './sidecar-client'
import { renderFacets, initFacets } from './facets'
import { appendRunOutput, appendDetailOutput, clearSurfaceOutput, clearSurfaceImages, setSurfaceStatusDot, renderSurfaceImages } from './output'
import { initGallery, renderGalleryGrid, renderToolboxGrid } from './gallery'
import { openDetail, closeDetail, saveExample, updateTitleDirty, initDetail, runFromDetail, runFromCard, renderDetailHistory, refreshDetailHistory } from './detail'
import { initRunner, runnerRun } from './runner'
import { loadAndRenderArgs, collectArgsFromForm, renderArgsForm, hideArgsPanel, requiredArgsMissing, applyArgsToForm } from './args-form'
import { refreshDetailAssets, uploadDetailAssets } from './assets'
import { recordHistory, loadHistory, persistHistory, clearHistory, historyAsLog, exportHistoryLog, rerunFromHistory, initHistoryPanel, openHistoryPanel, closeHistoryPanel, renderHistoryPanel, updateHistoryBadge, formatHistoryTime, formatDuration } from './history'
import { loadFavorites, persistFavorites, isFavorite, toggleFavorite, refreshFavoritesViews, updateFavChip, updateActionBarFav, initFavorites } from './favorites'
import { initAI, loadAISettings, openAISettings, closeAISettings, saveAISettings, openAIPanel, closeAIPanel, showStopButton, stopAI, setAIStatus, appendAIOutput, copyAIOutput, getSelectedOrAllCode, explainSelectedCode } from './ai'
import { initMonaco } from './monaco-editor'

// 应用编排
import {
  bootstrap, setSidecarStatus, getCurrentTheme, applyTheme, toggleTheme,
  loadExamples, currentFilterQuery, filterContext, applyFilters, applyAllFilters,
  rebuildIndexes, rebuildRunStatusIndex, loadViewPrefs, persistViewPrefs,
  runExample, stopRun, downloadResultImage, switchView
} from './app'

// 兼容全局变量（冒烟测试探针 / 手工调试）
Object.assign(window, {
  state, els, THEMES,
  ...utils,
  FilterEngine,
  api,
  renderFacets, initFacets,
  appendRunOutput, appendDetailOutput, clearSurfaceOutput, clearSurfaceImages, setSurfaceStatusDot, renderSurfaceImages,
  initGallery, renderGalleryGrid, renderToolboxGrid,
  openDetail, closeDetail, saveExample, updateTitleDirty, initDetail, runFromDetail, runFromCard, renderDetailHistory, refreshDetailHistory,
  initRunner, runnerRun,
  loadAndRenderArgs, collectArgsFromForm, renderArgsForm, hideArgsPanel, requiredArgsMissing, applyArgsToForm,
  refreshDetailAssets, uploadDetailAssets,
  recordHistory, loadHistory, persistHistory, clearHistory, historyAsLog, exportHistoryLog, rerunFromHistory, initHistoryPanel, openHistoryPanel, closeHistoryPanel, renderHistoryPanel, updateHistoryBadge, formatHistoryTime, formatDuration,
  loadFavorites, persistFavorites, isFavorite, toggleFavorite, refreshFavoritesViews, updateFavChip, updateActionBarFav, initFavorites,
  initAI, loadAISettings, openAISettings, closeAISettings, saveAISettings, openAIPanel, closeAIPanel, showStopButton, stopAI, setAIStatus, appendAIOutput, copyAIOutput, getSelectedOrAllCode, explainSelectedCode,
  initMonaco,
  bootstrap, setSidecarStatus, getCurrentTheme, applyTheme, toggleTheme,
  loadExamples, currentFilterQuery, filterContext, applyFilters, applyAllFilters,
  rebuildIndexes, rebuildRunStatusIndex, loadViewPrefs, persistViewPrefs,
  runExample, stopRun, downloadResultImage, switchView
})

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
  try {
    bootstrap()
  } catch (err) {
    console.error('[renderer] bootstrap failed:', err)
  }
})

console.log('[vite] renderer entry loaded (v0.6 gallery-first)')
