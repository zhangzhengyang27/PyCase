// preload.ts：通过 contextBridge 向渲染进程暴露安全的 sidecar API。

import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron'

// 主题恢复（首帧前）：渲染层 main.ts 要等模块加载完才执行，light 用户会闪暗色。
// DOM 在 preload 阶段已可用，此处提前设 data-theme；失败则回落到 index.html 的 dark 兜底。
// 偏好值为 dark/light/system 三态，system 按 prefers-color-scheme 现场解析。
// 本文件在无 DOM lib 的 node tsconfig 下编译，globalThis 经结构类型访问。
try {
  const savedTheme = localStorage.getItem('app-theme') || 'dark'
  const matchMedia = (globalThis as unknown as { matchMedia?: (query: string) => { matches: boolean } }).matchMedia
  const resolved =
    savedTheme === 'system'
      ? matchMedia?.('(prefers-color-scheme: dark)')?.matches
        ? 'dark'
        : 'light'
      : savedTheme
  const root = (globalThis as unknown as { document?: { documentElement: { setAttribute(key: string, value: string): void } } })
    .document?.documentElement
  if (resolved && root) root.setAttribute('data-theme', resolved)
} catch {
  // localStorage 不可用时保持默认主题
}

// 类型定义：渲染层通过 window.sidecar.* 调用
export interface SidecarAPI {
  // 方法调用（返回 Promise）
  ping: () => Promise<unknown>
  listExamples: () => Promise<unknown>
  getExample: (id: string) => Promise<unknown>
  parseArgs: (id: string) => Promise<unknown>
  saveExample: (id: string, code: string) => Promise<unknown>
  runExample: (params: Record<string, unknown>) => Promise<unknown>
  stopRun: (runId: string) => Promise<unknown>
  uploadAsset: (params: Record<string, unknown>) => Promise<unknown>
  listAssets: (id: string) => Promise<unknown>
  deleteAsset: (params: Record<string, unknown>) => Promise<unknown>
  downloadResultImage: (url: string, defaultName?: string) => Promise<unknown>
  saveTextFile: (params: { content?: string; defaultName?: string; filters?: unknown[] }) => Promise<unknown>
  restart: () => Promise<unknown>

  // 用户示例集合（导入向导 / 删除管理）
  pickDirectory: () => Promise<unknown>
  scanImportSource: (sourcePath: string) => Promise<unknown>
  importExamples: (params: { source_path: string; name?: string }) => Promise<unknown>
  deleteExample: (id: string) => Promise<unknown>

  // 用户数据（userData 下的小 JSON：history / favorites / aiSettings）
  store: {
    get: (name: string) => Promise<unknown>
    set: (name: string, value: unknown) => Promise<unknown>
  }

  // AI 代码解释（DeepSeek）：key 只在主进程侧注入，前端不接触明文
  ai: {
    getSettings: () => Promise<unknown>
    setSettings: (patch: Record<string, unknown>) => Promise<unknown>
    explain: (code: string, fileName?: string) => Promise<unknown>
    stop: (runId: string) => Promise<unknown>
  }

  // 事件订阅（sidecar -> 渲染进程的通知）
  onStatus: (callback: (data: unknown) => void) => () => void
  onRunOutput: (callback: (data: unknown) => void) => () => void
  onRunFinished: (callback: (data: unknown) => void) => () => void
  onRunImages: (callback: (data: unknown) => void) => () => void

  // 通用 sidecar 通知订阅（method 即 sidecar 发出的 notification 方法名，如 ai_explain_chunk）
  onNotification: (method: string, callback: (data: unknown) => void) => () => void
}

type Unsubscribe = () => void

function subscribe(channel: string, callback: (data: unknown) => void): Unsubscribe {
  const handler = (_e: IpcRendererEvent, data: unknown) => callback(data)
  ipcRenderer.on(channel, handler)
  return () => ipcRenderer.removeListener(channel, handler)
}

const sidecarAPI: SidecarAPI = {
  // 方法调用（返回 Promise）
  ping: () => ipcRenderer.invoke('sidecar:ping'),
  listExamples: () => ipcRenderer.invoke('sidecar:listExamples'),
  getExample: (id: string) => ipcRenderer.invoke('sidecar:getExample', id),
  parseArgs: (id: string) => ipcRenderer.invoke('sidecar:parseArgs', id),
  saveExample: (id: string, code: string) => ipcRenderer.invoke('sidecar:saveExample', { id, code }),
  runExample: (params: Record<string, unknown>) => ipcRenderer.invoke('sidecar:runExample', params),
  stopRun: (runId: string) => ipcRenderer.invoke('sidecar:stopRun', runId),
  uploadAsset: (params: Record<string, unknown>) => ipcRenderer.invoke('sidecar:uploadAsset', params),
  listAssets: (id: string) => ipcRenderer.invoke('sidecar:listAssets', id),
  deleteAsset: (params: Record<string, unknown>) => ipcRenderer.invoke('sidecar:deleteAsset', params),
  downloadResultImage: (url: string, defaultName?: string) =>
    ipcRenderer.invoke('file:downloadResultImage', { url, defaultName }),
  saveTextFile: (params: { content?: string; defaultName?: string; filters?: unknown[] }) =>
    ipcRenderer.invoke('file:saveText', params),
  restart: () => ipcRenderer.invoke('sidecar:restart'),

  // 用户示例集合（导入向导 / 删除管理）
  pickDirectory: () => ipcRenderer.invoke('file:pickDirectory'),
  scanImportSource: (sourcePath: string) => ipcRenderer.invoke('sidecar:scanExamples', { source_path: sourcePath }),
  importExamples: (params: { source_path: string; name?: string }) =>
    ipcRenderer.invoke('sidecar:importExamples', params),
  deleteExample: (id: string) => ipcRenderer.invoke('sidecar:deleteExample', { id }),

  // 用户数据（userData 下的小 JSON：history / favorites / aiSettings）
  store: {
    get: (name: string) => ipcRenderer.invoke('store:get', name),
    set: (name: string, value: unknown) => ipcRenderer.invoke('store:set', name, value)
  },

  // AI 代码解释（DeepSeek）：key 只在主进程侧注入，前端不接触明文
  ai: {
    getSettings: () => ipcRenderer.invoke('ai:getSettings'),
    setSettings: (patch: Record<string, unknown>) => ipcRenderer.invoke('ai:setSettings', patch),
    explain: (code: string, fileName?: string) => ipcRenderer.invoke('ai:explain', { code, file_name: fileName }),
    stop: (runId: string) => ipcRenderer.invoke('ai:stop', runId)
  },

  // 事件订阅（sidecar -> 渲染进程的通知）
  onStatus: (callback: (data: unknown) => void) => subscribe('sidecar:status', callback),
  onRunOutput: (callback: (data: unknown) => void) => subscribe('sidecar:run_output', callback),
  onRunFinished: (callback: (data: unknown) => void) => subscribe('sidecar:run_finished', callback),
  onRunImages: (callback: (data: unknown) => void) => subscribe('sidecar:run_images', callback),

  // 通用 sidecar 通知订阅（method 即 sidecar 发出的 notification 方法名，如 ai_explain_chunk）
  onNotification: (method: string, callback: (data: unknown) => void) => subscribe(`sidecar:${method}`, callback)
}

contextBridge.exposeInMainWorld('sidecar', sidecarAPI)
