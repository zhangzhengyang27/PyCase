// state.ts：全局状态、主题配置与 DOM 引用（v0.6 画廊优先架构）
// 三视图：gallery（示例画廊）/ toolbox（工具箱）/ runner（代码运行器）+ 单例详情页

// ---------------------------------------------------------------------------
// 类型定义
// ---------------------------------------------------------------------------
export interface ExampleItem {
  id: string
  name: string
  category: string
  path: string
  code?: string
  description?: string
  tags?: string[]
  args?: string[]
  title?: string
  quality_score?: number
  _importTags?: string[]
}

export interface TreeNode {
  name: string
  path: string
  children?: TreeNode[]
  example?: ExampleItem
}

export interface RunHistoryEntry {
  ts: string
  id: string
  name: string
  args: string[]
  duration_ms: number
  exit_code: number
  ok: boolean
}

export interface AISettings {
  hasKey: boolean
  model: string
  baseUrl: string
  acknowledged: boolean
}

// ---------------------------------------------------------------------------
// 全局状态
// ---------------------------------------------------------------------------
export const state: any = {
  examples: [] as ExampleItem[],
  filtered: [] as ExampleItem[],

  // 视图：gallery | toolbox | runner
  activeView: 'gallery' as 'gallery' | 'toolbox' | 'runner',
  searchQuery: '',
  toolSearchQuery: '',

  // 画廊筛选维度（经 filter-engine 组合）
  activeTheme: 'all' as string,
  minQuality: 0 as number,
  sortBy: 'quality_desc' as 'quality_desc' | 'name' | 'last_run',
  galleryLimit: 120 as number,

  // 详情页（单例，画廊/工具箱共用）：当前示例 + 打开来源视图
  selectedId: null as string | null,
  detailFrom: 'gallery' as 'gallery' | 'toolbox',

  // 运行器：快速选中的示例 id
  runnerSelectedId: null as string | null,

  // 运行状态（同一时刻至多一个运行）
  currentRunId: null as string | null,
  isRunning: false,
  // 输出汇（本次运行输出写到哪个面板）：detail | runner
  runSink: null as 'detail' | 'runner' | null,
  currentRunMeta: null as { id: string; name: string; args: string[]; startedAt: number } | null,

  // 编辑器（Monaco 实例驻留详情页源码区）
  editor: null as any,
  monaco: null as any,
  isDirty: false,
  originalCode: '',
  currentArgs: [] as string[],

  // 运行历史（userData/history.json，由 history.ts 管理）
  runHistory: [] as RunHistoryEntry[],
  // 收藏的示例 id 集合（userData/favorites.json，由 favorites.ts 管理）
  favorites: new Set<string>(),
  favOnly: false,
  // 多维筛选：运行状态 all/ok/failed/never；选中的标签集合
  activeRunStatus: 'all' as 'all' | 'ok' | 'failed' | 'never',
  activeTags: new Set<string>(),
  // 示例 id → 最近运行状态 / 最近运行时间（由 filter-engine 从 runHistory 构建）
  runStatusIndex: new Map<string, 'ok' | 'failed'>(),
  lastRunIndex: new Map<string, number>(),

  // AI 代码解释设置
  aiSettings: { hasKey: false, model: 'deepseek-chat', baseUrl: 'https://api.deepseek.com', acknowledged: false } as AISettings,
  // AI 解释当前 run_id（用于匹配流式通知）
  aiRunId: ''
}

// ---------------------------------------------------------------------------
// 主题配置：已抽至独立的纯模块 themes.ts（Vue 渲染层复用），此处 re-export 保持旧导入路径
// ---------------------------------------------------------------------------
export { THEMES, type ThemeConfig } from './themes'

// ---------------------------------------------------------------------------
// DOM 引用
// ---------------------------------------------------------------------------
const $ = (id: string): HTMLElement | null => document.getElementById(id)

export const els: any = {
  // 顶部导航
  navSegments: document.querySelectorAll('.nav-segment'),
  btnRefresh: $('btn-refresh'),
  btnThemeToggle: $('btn-theme-toggle'),
  // 布局容器
  viewGallery: $('view-gallery'),
  viewToolbox: $('view-toolbox'),
  viewRunner: $('view-runner'),
  detailPage: $('detail-page'),
  // 画廊
  gallerySearch: $('gallery-search') as HTMLInputElement | null,
  galleryFacets: $('gallery-facets'),
  galleryGrid: $('gallery-grid'),
  // 工具箱
  toolboxSearch: $('toolbox-search') as HTMLInputElement | null,
  toolboxFacets: $('toolbox-facets'),
  toolboxGrid: $('toolbox-grid'),
  // 详情页
  detailBack: $('detail-back'),
  detailIcon: $('detail-icon'),
  detailTitle: $('detail-title'),
  detailTags: $('detail-tags'),
  detailQuality: $('detail-quality'),
  detailCategory: $('detail-category'),
  btnFavToggle: $('btn-fav-toggle'),
  btnSave: $('btn-save'),
  btnStop: $('btn-stop'),
  btnRun: $('btn-run'),
  monacoContainer: $('monaco-container'),
  // 详情页参数表单
  argsPanel: $('args-panel'),
  argsHeader: $('args-header'),
  argsForm: $('args-form'),
  argsCount: $('args-count'),
  // 详情页下半区标签（终端输出 / 资源 / 历史）
  detailTabBtns: document.querySelectorAll('.detail-tab'),
  detailTabBtnOutput: $('detail-tab-btn-output'),
  detailTabBtnAssets: $('detail-tab-btn-assets'),
  detailTabBtnHistory: $('detail-tab-btn-history'),
  detailTabOutput: $('detail-tab-output'),
  detailTabAssets: $('detail-tab-assets'),
  detailTabHistory: $('detail-tab-history'),
  detailAssetsFile: $('detail-assets-file') as HTMLInputElement | null,
  detailAssetsUpload: $('detail-assets-upload'),
  detailAssetsList: $('detail-assets-list'),
  detailAssetsCount: $('detail-assets-count'),
  detailHistoryCount: $('detail-history-count'),
  detailOutputStatusDot: $('detail-output-status-dot'),
  btnClearOutput: $('detail-btn-clear'),
  detailOutputViewer: $('detail-output-viewer'),
  detailOutputImages: $('detail-output-images'),
  // 运行器
  runnerSearch: $('runner-search') as HTMLInputElement | null,
  runnerResults: $('runner-results'),
  runnerCode: $('runner-code'),
  runnerTitle: $('runner-title'),
  runnerArgs: $('runner-args') as HTMLInputElement | null,
  runnerRun: $('runner-run'),
  runnerStop: $('runner-stop'),
  runnerStatusDot: $('runner-status-dot'),
  runnerClear: $('runner-clear'),
  runnerOutputViewer: $('runner-output-viewer'),
  runnerOutputImages: $('runner-output-images'),
  // 底部状态栏
  statusSidecarDot: $('status-sidecar-dot'),
  statusSidecarText: $('status-sidecar-text'),
  statusCount: $('status-count'),
  statusRun: $('status-run')
}
