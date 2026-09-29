// 协议名表（跨语言单一来源 = shared/protocol.json）。
//
// 为什么 TS 侧还要写一遍：JSON 无法给出字面量联合类型，客户端需要
// `ProtocolMethod` / `NotificationChannel` 这类编译期约束；两处一致性由契约测试钉住
// （tests/test_guard_protocol.py 的 TS 对照见 src/renderer/src/__tests__/protocol.spec.ts）。
//
// 增删方法：改 protocol.json + 本文件 + docs/redesign-data-contract.md §5。

/** sidecar 的 JSON-RPC 方法名（下划线口径，与 Python METHODS 表逐字对应）。 */
export const RPC_METHODS = [
  'ping',
  'env_status',
  'set_run_env',
  'list_examples',
  'get_example',
  'search_examples',
  'parse_args',
  'save_example',
  'run_example',
  'stop_run',
  'upload_asset',
  'list_assets',
  'delete_asset',
  'scan_import_source',
  'import_examples',
  'delete_example',
  'explain_code',
  'stop_ai'
] as const

export type RpcMethod = (typeof RPC_METHODS)[number]

/** sidecar → 渲染层的通知（主进程按 `sidecar:<name>` 转发）。 */
export const NOTIFICATIONS = [
  'sidecar_ready',
  'run_output',
  'run_finished',
  'run_images',
  'env_progress',
  'ai_explain_chunk',
  'ai_explain_done',
  'ai_explain_error'
] as const

export type NotificationName = (typeof NOTIFICATIONS)[number]

/** 主进程本地事件（不经 sidecar）。 */
export const LOCAL_EVENTS = ['status'] as const

/** preload 暴露的命名空间分组（非 JSON-RPC，走 IPC）。 */
export const NAMESPACES = {
  store: ['get', 'set'],
  app: ['info', 'openLog'],
  env: ['status', 'setRunEnv', 'onProgress'],
  win: ['minimize', 'toggleMaximize', 'close', 'isMaximized', 'onMaximizedChange'],
  ai: ['getSettings', 'setSettings', 'explain', 'stop'],
  file: ['pickDirectory', 'saveTextFile', 'downloadResultImage']
} as const
