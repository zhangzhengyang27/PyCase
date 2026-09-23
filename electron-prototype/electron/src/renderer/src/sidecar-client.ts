// sidecar-client.ts：渲染层访问 sidecar 的唯一入口
// 封装 preload 注入的 window.sidecar 桥：
//   1. 统一 Promise 调用与错误归一化（错误带方法名，便于定位）；
//   2. 事件订阅中心：同一通知支持多个订阅者，订阅返回退订函数；
//   3. 重请求单飞：listExamples 并发调用时复用同一个 Promise。
// 依赖：preload（window.sidecar）。本模块无其他全局依赖。

const bridge = window.sidecar
if (!bridge) {
  console.error('[sidecar-client] window.sidecar 不存在：preload 是否正确加载？')
}

// -------------------------------------------------------------------------
// 事件订阅中心（status / runOutput / runFinished / runImages / aiExplain*）
// -------------------------------------------------------------------------
type SidecarChannel = 'status' | 'runOutput' | 'runFinished' | 'runImages' | 'aiExplainChunk' | 'aiExplainDone' | 'aiExplainError'

const channels: SidecarChannel[] = ['status', 'runOutput', 'runFinished', 'runImages', 'aiExplainChunk', 'aiExplainDone', 'aiExplainError']
const listeners: Record<SidecarChannel, Array<(data: any) => void>> = Object.fromEntries(channels.map((c) => [c, []])) as unknown as Record<SidecarChannel, Array<(data: any) => void>>

function safeDispatch(channel: SidecarChannel, data: any): void {
  listeners[channel].slice().forEach((fn) => {
    try {
      fn(data)
    } catch (err) {
      console.error(`[sidecar-client] ${channel} 订阅者异常:`, err)
    }
  })
}

// preload 的 onXxx 只允许注册一次，这里统一桥接到订阅中心
bridge.onStatus((data: any) => safeDispatch('status', data))
bridge.onRunOutput((data: any) => safeDispatch('runOutput', data))
bridge.onRunFinished((data: any) => safeDispatch('runFinished', data))
bridge.onRunImages((data: any) => safeDispatch('runImages', data))
// AI 流式解释通知（sidecar -> 主进程转发 -> 这里）
bridge.onNotification('ai_explain_chunk', (data: any) => safeDispatch('aiExplainChunk', data))
bridge.onNotification('ai_explain_done', (data: any) => safeDispatch('aiExplainDone', data))
bridge.onNotification('ai_explain_error', (data: any) => safeDispatch('aiExplainError', data))

export function on(channel: SidecarChannel, fn: (data: any) => void): () => void {
  if (!listeners[channel]) throw new Error(`未知 sidecar 事件: ${channel}`)
  listeners[channel].push(fn)
  return () => off(channel, fn)
}

export function off(channel: SidecarChannel, fn: (data: unknown) => void): void {
  const arr = listeners[channel]
  const idx = arr.indexOf(fn)
  if (idx >= 0) arr.splice(idx, 1)
}

// -------------------------------------------------------------------------
// 请求封装：错误归一化（保留原始 message，附加方法名前缀）
// -------------------------------------------------------------------------
async function request(method: string, fn: (...args: any[]) => Promise<any>, args: any[]): Promise<any> {
  try {
    return await fn.apply(bridge, args)
  } catch (err) {
    const message = err && err instanceof Error ? err.message : String(err)
    const wrapped = new Error(`[${method}] ${message}`)
    console.error('[sidecar-client] 请求失败:', wrapped.message)
    throw wrapped
  }
}

// listExamples 物化上千示例较慢，短时间内的并发调用复用同一 Promise（单飞）
let listExamplesInflight: Promise<unknown> | null = null

export interface RunExampleParams {
  id: string
  code?: string
  args?: string[]
  cwd?: string
}

export interface UploadAssetParams {
  exampleId: string
  fileName: string
  data: ArrayBuffer | string
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

export const api = {
  // 事件
  on,
  off,

  // 健康检查 / 数据
  ping: () => bridge.ping(),
  listExamples() {
    if (!listExamplesInflight) {
      listExamplesInflight = request('listExamples', bridge.listExamples as (...args: unknown[]) => Promise<unknown>, []).finally(() => {
        listExamplesInflight = null
      })
    }
    return listExamplesInflight
  },
  getExample: (id: string) => request('getExample', bridge.getExample as (...args: unknown[]) => Promise<unknown>, [id]),
  parseArgs: (id: string) => request('parseArgs', bridge.parseArgs as (...args: unknown[]) => Promise<unknown>, [id]),
  saveExample: (id: string, code: string) => request('saveExample', bridge.saveExample as (...args: unknown[]) => Promise<unknown>, [id, code]),

  // 运行控制
  runExample: (params: RunExampleParams) => request('runExample', bridge.runExample as (...args: unknown[]) => Promise<unknown>, [params]),
  stopRun: (runId: string) => request('stopRun', bridge.stopRun as (...args: unknown[]) => Promise<unknown>, [runId]),

  // 资源管理
  uploadAsset: (params: UploadAssetParams) => request('uploadAsset', bridge.uploadAsset as (...args: unknown[]) => Promise<unknown>, [params]),
  listAssets: (id: string) => request('listAssets', bridge.listAssets as (...args: unknown[]) => Promise<unknown>, [id]),
  deleteAsset: (params: DeleteAssetParams) => request('deleteAsset', bridge.deleteAsset as (...args: unknown[]) => Promise<unknown>, [params]),
  downloadResultImage: (url: string, defaultName: string) =>
    request('downloadResultImage', bridge.downloadResultImage as (...args: unknown[]) => Promise<unknown>, [url, defaultName]),
  saveTextFile: (params: SaveTextFileParams) => request('saveTextFile', bridge.saveTextFile as (...args: unknown[]) => Promise<unknown>, [params]),

  // 用户示例集合（导入向导 / 删除管理）
  pickDirectory: () => request('file:pickDirectory', () => bridge.pickDirectory(), []),
  scanImportSource: (sourcePath: string) =>
    request('scanImportSource', (p: string) => bridge.scanImportSource(p), [sourcePath]),
  importExamples: (params: ImportExamplesParams) =>
    request(
      'importExamples',
      (p: ImportExamplesParams) => bridge.importExamples({ source_path: p.sourcePath, name: p.name }),
      [params]
    ),
  deleteExample: (id: string) => request('deleteExample', (i: string) => bridge.deleteExample(i), [id]),

  // 用户数据存储（主进程落盘到 userData）
  storeGet: (name: string) => request('store:get', (n: string) => bridge.store.get(n), [name]),
  storeSet: (name: string, value: unknown) => request('store:set', (n: string, v: unknown) => bridge.store.set(n, v), [name, value]),

  // AI 代码解释（DeepSeek）：key 只在主进程侧，前端不接触明文
  aiGetSettings: () => request('ai:getSettings', () => bridge.ai.getSettings(), []),
  aiSetSettings: (patch: Record<string, unknown>) => request('ai:setSettings', (p: Record<string, unknown>) => bridge.ai.setSettings(p), [patch]),
  aiExplain: (code: string, fileName: string) =>
    request('ai:explain', (c: string, f: string) => bridge.ai.explain(c, f), [code, fileName]),
  aiStop: (runId: string) => request('ai:stop', (id: string) => bridge.ai.stop(id), [runId]),

  // 其他
  restart: () => bridge.restart()
}
