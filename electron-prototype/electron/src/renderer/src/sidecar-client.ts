// sidecar-client.ts：渲染层访问主进程/sidecar 的唯一入口（类型化）。
//
// 分层：
//   window.sidecar（preload 暴露，出入参类型见 shared/protocol.ts）
//     ↓ 本模块：错误归一化 / 单飞 / 事件订阅中心
//   api.*（渲染层其余代码只认这一层；不直接摸 window.sidecar）
//
// 契约来源：shared/protocol.ts（与 Python METHODS 表由契约测试双端钉住）；
// 事件通道名与 protocol.json 的 notifications / local_events 对齐。

import type {
  AiExplainChunkEvent,
  AiExplainDoneEvent,
  AiExplainErrorEvent,
  AiSettingsView,
  AppInfo,
  ArgSpec,
  AssetInfo,
  DownloadResult,
  EnvPhase,
  ExampleDetail,
  ImportPreviewFile,
  ListExamplesResult,
  OpenLogResult,
  PickDirectoryResult,
  RunFinishedEvent,
  RunImagesEvent,
  RunOutputEvent,
  SaveTextResult,
  SearchHit,
  SidecarStatusEvent,
  StorageReport,
  VersionInfo
} from '../../../../shared/protocol'

const bridge = window.sidecar
if (!bridge) {
  console.error('[sidecar-client] window.sidecar 不存在：preload 是否正确加载？')
}

// -------------------------------------------------------------------------
// 事件订阅中心（status / run* / aiExplain* / envProgress / maximized）
// -------------------------------------------------------------------------
export interface EventPayloads {
  /** sidecar 进程状态（主进程本地事件） */
  status: SidecarStatusEvent
  runOutput: RunOutputEvent
  runFinished: RunFinishedEvent
  runImages: RunImagesEvent
  aiExplainChunk: AiExplainChunkEvent
  aiExplainDone: AiExplainDoneEvent
  aiExplainError: AiExplainErrorEvent
  /** 环境准备进度（首启页阶段推进；env_status 的增量推送） */
  envProgress: EnvPhase
  /** 窗口最大化状态变化（Windows 自绘标题栏按钮态） */
  maximized: { maximized: boolean }
}

export type EventChannel = keyof EventPayloads
type Listener<K extends EventChannel> = (data: EventPayloads[K]) => void

const EVENT_CHANNELS: EventChannel[] = [
  'status',
  'runOutput',
  'runFinished',
  'runImages',
  'aiExplainChunk',
  'aiExplainDone',
  'aiExplainError',
  'envProgress',
  'maximized'
]

const listeners = Object.fromEntries(EVENT_CHANNELS.map((c) => [c, [] as Listener<EventChannel>[]])) as {
  [K in EventChannel]: Listener<K>[]
}

function safeDispatch<K extends EventChannel>(channel: K, data: EventPayloads[K]): void {
  for (const fn of [...listeners[channel]]) {
    try {
      ;(fn as Listener<K>)(data)
    } catch (err) {
      console.error(`[sidecar-client] ${channel} 订阅者异常:`, err)
    }
  }
}

/** 订阅一个事件通道；返回退订函数。 */
export function on<K extends EventChannel>(channel: K, fn: Listener<K>): () => void {
  const arr = listeners[channel]
  if (!arr) throw new Error(`未知 sidecar 事件: ${channel}`)
  ;(arr as Listener<K>[]).push(fn)
  return () => off(channel, fn)
}

/** 退订（与 on 的返回函数等价，保留旧签名）。 */
export function off<K extends EventChannel>(channel: K, fn: Listener<K>): void {
  const arr = listeners[channel] as Listener<K>[]
  const idx = arr.indexOf(fn)
  if (idx >= 0) arr.splice(idx, 1)
}

// preload 的 onXxx 只允许注册一次，这里统一桥接到订阅中心（模块加载即挂好）
bridge.onStatus((data) => safeDispatch('status', data))
bridge.onRunOutput((data) => safeDispatch('runOutput', data))
bridge.onRunFinished((data) => safeDispatch('runFinished', data))
bridge.onRunImages((data) => safeDispatch('runImages', data))
bridge.env.onProgress((data) => safeDispatch('envProgress', data))
bridge.win.onMaximizedChange((data) => safeDispatch('maximized', data))
bridge.onNotification('ai_explain_chunk', (data) => safeDispatch('aiExplainChunk', data as AiExplainChunkEvent))
bridge.onNotification('ai_explain_done', (data) => safeDispatch('aiExplainDone', data as AiExplainDoneEvent))
bridge.onNotification('ai_explain_error', (data) => safeDispatch('aiExplainError', data as AiExplainErrorEvent))

// -------------------------------------------------------------------------
// 请求封装：错误归一化（保留原始 message，附加方法名前缀）
// -------------------------------------------------------------------------
/** 带协议错误码的客户端错误（-326xx = JSON-RPC 标准，-3200x = 主进程本地补充）。 */
export interface SidecarError extends Error {
  code?: number
  method?: string
}

async function request<T>(method: string, fn: () => Promise<T>): Promise<T> {
  try {
    return await fn()
  } catch (err) {
    const message = err && err instanceof Error ? err.message : String(err)
    const wrapped = new Error(`[${method}] ${message}`) as SidecarError
    wrapped.code = (err as SidecarError)?.code
    wrapped.method = method
    console.error('[sidecar-client] 请求失败:', wrapped.message)
    throw wrapped
  }
}

// listExamples 建索引较慢，短时间内的并发调用复用同一 Promise（单飞）
let listExamplesInflight: Promise<ListExamplesResult> | null = null

export interface RunExampleParams {
  id: string
  args?: string[]
  timeout?: number
  /** 可选代码覆盖（交互工具抽屉）：非空字符串 ≤64000 字符，在一次性 adhoc 工作区运行 */
  code?: string
}

export interface UploadAssetParams {
  exampleId: string
  fileName: string
  /** base64（不带 data: 前缀）；调用方负责编码（主进程按 20MB 校验） */
  data: string
}

export interface DeleteAssetParams {
  exampleId: string
  fileName: string
}

export interface SaveTextFileParams {
  defaultName: string
  content: string
}

export interface ImportExamplesParams {
  sourcePath: string
  name?: string
}

/**
 * RPC 方法 → 客户端调用路径（协议名 → api 上的路径）。
 * 契约测试据此断言「protocol.json 里的每个方法都已接线」，漏一个即红。
 */
export const RPC_BINDINGS: Record<string, string> = {
  ping: 'ping',
  env_status: 'envStatus',
  set_run_env: 'setRunEnv',
  list_examples: 'listExamples',
  get_example: 'getExample',
  search_examples: 'searchExamples',
  parse_args: 'parseArgs',
  save_example: 'saveExample',
  run_example: 'runExample',
  stop_run: 'stopRun',
  upload_asset: 'uploadAsset',
  list_assets: 'listAssets',
  delete_asset: 'deleteAsset',
  scan_import_source: 'scanImportSource',
  import_examples: 'importExamples',
  delete_example: 'deleteExample',
  explain_code: 'aiExplain',
  stop_ai: 'aiStop',
  storage_report: 'storageReport',
  clean_workspace: 'cleanWorkspace',
  reclaim_legacy_cache: 'reclaimLegacyCache',
  list_versions: 'listVersions',
  read_version: 'readVersion',
  restore_version: 'restoreVersion',
  install_example_deps: 'installExampleDeps'
}

/** 渲染层唯一的数据/命令入口（类型与 shared/protocol.ts 对齐）。 */
export const api = {
  // 事件
  on,
  off,

  // 健康检查 / 数据
  ping: (): Promise<{ status: 'ok'; python: string }> => request('ping', () => bridge.ping()),
  listExamples(): Promise<ListExamplesResult> {
    if (!listExamplesInflight) {
      listExamplesInflight = request('listExamples', () => bridge.listExamples()).finally(() => {
        listExamplesInflight = null
      })
    }
    return listExamplesInflight
  },
  getExample: (id: string): Promise<ExampleDetail> => request('getExample', () => bridge.getExample(id)),
  parseArgs: (id: string): Promise<{ args: ArgSpec[]; count: number }> =>
    request('parseArgs', () => bridge.parseArgs(id)),
  saveExample: (
    id: string,
    code: string
  ): Promise<{ status: 'saved'; id: string; json_file: string | null; path: string }> =>
    request('saveExample', () => bridge.saveExample(id, code)),

  // 运行控制
  runExample: (params: RunExampleParams): Promise<{ run_id: string }> =>
    request('runExample', () => bridge.runExample(params)),
  stopRun: (runId: string): Promise<{ status: 'terminating' | 'pending_terminate'; run_id: string }> =>
    request('stopRun', () => bridge.stopRun(runId)),

  // 资源管理
  uploadAsset: (
    params: UploadAssetParams
  ): Promise<{ status: 'uploaded'; filename: string; size: number; path: string; assets: AssetInfo[] }> =>
    request('uploadAsset', () =>
      bridge.uploadAsset({ id: params.exampleId, filename: params.fileName, data: params.data })
    ),
  listAssets: (id: string): Promise<{ assets: AssetInfo[] }> => request('listAssets', () => bridge.listAssets(id)),
  deleteAsset: (params: DeleteAssetParams): Promise<{ deleted: string; assets: AssetInfo[] }> =>
    request('deleteAsset', () => bridge.deleteAsset({ id: params.exampleId, filename: params.fileName })),
  downloadResultImage: (url: string, defaultName = ''): Promise<DownloadResult> =>
    request('downloadResultImage', () => bridge.downloadResultImage(url, defaultName)),
  saveTextFile: (params: SaveTextFileParams): Promise<SaveTextResult> =>
    request('saveTextFile', () => bridge.saveTextFile({ content: params.content, defaultName: params.defaultName })),

  // 用户示例集合（导入向导 / 删除管理）
  pickDirectory: (): Promise<PickDirectoryResult> => request('file:pickDirectory', () => bridge.pickDirectory()),
  pickFile: (params: {
    title?: string
    extensions?: string[]
  }): Promise<{ canceled: boolean; path?: string; name?: string }> =>
    request('file:pickFile', () => bridge.pickFile(params)),
  scanImportSource: (
    sourcePath: string
  ): Promise<{ total: number; files: ImportPreviewFile[]; skipped: { file: string; reason: string }[] }> =>
    request('scanImportSource', () => bridge.scanImportSource(sourcePath)),
  importExamples: (
    params: ImportExamplesParams
  ): Promise<{
    imported: number
    skipped: { file: string; reason: string }[]
    collection: string | null
    total?: number
  }> => request('importExamples', () => bridge.importExamples({ source_path: params.sourcePath, name: params.name })),
  deleteExample: (id: string): Promise<{ deleted: string; total: number }> =>
    request('deleteExample', () => bridge.deleteExample(id)),

  // 用户数据存储（主进程落盘到 userData）
  storeGet: (name: string): Promise<unknown> => request('store:get', () => bridge.store.get(name)),
  storeSet: (name: string, value: unknown): Promise<unknown> =>
    request('store:set', () => bridge.store.set(name, value)),

  // AI 代码解释（DeepSeek）：key 只在主进程侧，前端不接触明文
  aiGetSettings: (): Promise<AiSettingsView> => request('ai:getSettings', () => bridge.ai.getSettings()),
  aiSetSettings: (patch: Record<string, unknown>): Promise<{ ok: boolean; hasKey: boolean }> =>
    request('ai:setSettings', () => bridge.ai.setSettings(patch)),
  aiExplain: (code: string, fileName = ''): Promise<{ run_id: string; status?: string; error?: string }> =>
    request('ai:explain', () => bridge.ai.explain(code, fileName)),
  aiStop: (runId: string): Promise<{ status: string; run_id: string }> =>
    request('ai:stop', () => bridge.ai.stop(runId)),

  // 服务端检索（契约 §5：元数据内存匹配 + code 按需读文件）
  searchExamples: (query: string, limit = 50): Promise<{ query: string; hits: SearchHit[] }> =>
    request('search_examples', () => bridge.searchExamples(query, limit)),

  // 环境准备状态（A5.5 首启引导页 / 帮助面板）
  envStatus: (): Promise<EnvPhase> => request('env_status', () => bridge.env.status()),
  setRunEnv: (mode: 'shared' | 'system'): Promise<EnvPhase> => request('set_run_env', () => bridge.env.setRunEnv(mode)),

  // 应用信息与日志（帮助面板「环境信息」段、首启页「查看准备日志」）
  appInfo: (): Promise<AppInfo> => request('app:info', () => bridge.app.info()),
  openLog: (): Promise<OpenLogResult> => request('app:openLog', () => bridge.app.openLog()),

  // A6：存储治理（设置中心「存储」分区）
  storageReport: (): Promise<StorageReport> => request('storage_report', () => bridge.storageReport()),
  cleanWorkspace: (mode: 'clean' | 'all'): Promise<{ removed: number; kept: number; freed_bytes: number }> =>
    request('clean_workspace', () => bridge.cleanWorkspace(mode)),
  reclaimLegacyCache: (): Promise<{ removed: number; freed_bytes: number }> =>
    request('reclaim_legacy_cache', () => bridge.reclaimLegacyCache()),

  // A6：编辑历史（可恢复编辑）
  listVersions: (id: string): Promise<{ id: string; versions: VersionInfo[] }> =>
    request('list_versions', () => bridge.listVersions(id)),
  readVersion: (id: string, ts: string): Promise<{ id: string; ts: string; code: string }> =>
    request('read_version', () => bridge.readVersion(id, ts)),
  restoreVersion: (id: string, ts: string): Promise<{ id: string; restored: string }> =>
    request('restore_version', () => bridge.restoreVersion(id, ts)),

  // A6：缺依赖修复（失败恢复）
  installExampleDeps: (id: string): Promise<{ installed: string[]; failed: string[]; packages: string[] }> =>
    request('install_example_deps', () => bridge.installExampleDeps(id)),

  // 窗口控制（Windows 自绘标题栏三键；macOS 不展示但可用）
  win: {
    minimize: (): Promise<void> => request('window:minimize', () => bridge.win.minimize()),
    toggleMaximize: (): Promise<boolean> => request('window:toggleMaximize', () => bridge.win.toggleMaximize()),
    close: (): Promise<void> => request('window:close', () => bridge.win.close()),
    isMaximized: (): Promise<boolean> => request('window:isMaximized', () => bridge.win.isMaximized())
  },

  // 其他
  restart: (): Promise<{ status: string }> => bridge.restart()
}
