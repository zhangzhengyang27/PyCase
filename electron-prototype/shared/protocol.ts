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
  'stop_ai',
  'storage_report',
  'clean_workspace',
  'reclaim_legacy_cache',
  'list_versions',
  'read_version',
  'restore_version',
  'install_example_deps'
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

// ---------------------------------------------------------------------------
// 线上数据模型（wire models）
//
// 与 Python 侧逐字对应：ExampleMeta ← server._item_to_dict、ArgSpec ← _arg_specs、
// AssetInfo ← _collect_assets、EnvStatus ← _env_snapshot。改字段先改 Python 那边。
// ---------------------------------------------------------------------------

/** 可运行性派生状态（与 app/run_status.py 的五态 + unknown 一致）。 */
export type RunStatus = 'runnable' | 'missing_deps' | 'empty' | 'broken' | 'risky' | 'unknown'

/** HIGH 风险明细（运行前确认弹窗展示）。 */
export interface RiskFinding {
  description: string
  category: string
}

/** 列表/详情共用的示例元数据（v2：不含 code，源码经 get_example 按需取）。 */
export interface ExampleMeta {
  id: string
  name: string
  title: string
  category: string
  tags: string[]
  quality_score: number
  risk_high: boolean
  run_status: RunStatus
  /** 真实源码文件路径（v2 真相源；运行仍走工作区） */
  path: string
  source_dir: string | null
  run_pythonpath: string[]
  description: string
  /** 派生事实：第三方 import 清单（服务端算好，前端不再从 code 反推） */
  import_tags: string[]
  /** 派生事实：命中的主题 key（与 src/themes.ts 谓词同源） */
  theme_key: string | null
  collection?: string
  user_collection?: boolean
  risk_findings?: RiskFinding[]
}

/** get_example：元数据 + 源码。 */
export interface ExampleDetail extends ExampleMeta {
  code: string
}

/** list_examples 的目录树节点（目录节点无元数据字段）。 */
export interface ExampleTreeNode {
  name: string
  type: 'root' | 'collection' | 'example'
  is_dir: boolean
  category: string
  children: ExampleTreeNode[]
  id?: string
}

export interface ListExamplesResult {
  total: number
  categories: string[]
  examples: ExampleMeta[]
  tree: ExampleTreeNode | null
}

/** argparse 静态分析出的参数规格（运行表单渲染用）。 */
export interface ArgSpec {
  name: string
  flags: string[]
  dest: string
  type: string
  default?: unknown
  help: string
  choices: unknown[]
  required: boolean
  action: string
  is_positional: boolean
  nargs?: string | number | null
  metavar?: string | null
}

export interface AssetInfo {
  filename: string
  size: number
  modified: number
  is_image: boolean
}

/** 服务端检索命中：只回 id + 命中原因，前端按 id 取已有索引里的卡片数据。 */
export interface SearchHit {
  id: string
  reason: 'name' | 'tag' | 'description' | 'code'
}

/** 导入向导预览里的单个文件（不含 code 全文，只报大小）。 */
export interface ImportPreviewFile {
  id: string
  name: string
  tags: string[]
  requirements: string[]
  bytes: number
}

export interface EnvPhase {
  phase: 'starting' | 'preparing' | 'indexing' | 'warming' | 'ready' | 'failed'
  failed_at?: string
  started_at?: number
  error?: string
  mode: 'shared' | 'system'
  venv_path: string
  venv_ready: boolean
  python_version: string
  examples: number
  elapsed_ms: number
}

/** 历史版本条目（可恢复编辑）。 */
export interface VersionInfo {
  ts: string
  bytes: number
  sha256: string
}

/** 存储占用报告（工作区明细 + v1 旧根 + 编辑历史）。 */
export interface StorageReport {
  workspace: {
    root: string
    bytes: number
    max_bytes: number
    entries: { key: string; bytes: number; last_used: number; has_assets: boolean }[]
    asset_entries: number
  }
  legacy: { root: string; bytes: number; entries: number }
  history: { bytes: number }
}

export interface RunExampleParams {
  id: string
  args?: string[]
  timeout?: number
  [key: string]: unknown
}

export interface UploadAssetParams {
  id: string
  filename: string
  /** base64（不带 data: 前缀） */
  data: string
}

export interface SaveTextFileParams {
  content?: string
  defaultName?: string
  filters?: { name: string; extensions: string[] }[]
}

// ---------------------------------------------------------------------------
// RPC 契约：每个 sidecar 方法一行（Exhaustive 由类型系统保证：漏一个方法就编译失败）
// ---------------------------------------------------------------------------

export interface RpcContract {
  ping: { params: void; result: { status: 'ok'; python: string } }
  env_status: { params: void; result: EnvPhase }
  set_run_env: { params: { mode: 'shared' | 'system' }; result: EnvPhase }
  list_examples: { params: void; result: ListExamplesResult }
  get_example: { params: { id: string }; result: ExampleDetail }
  search_examples: { params: { query: string; limit?: number }; result: { query: string; hits: SearchHit[] } }
  parse_args: { params: { id?: string; code?: string }; result: { args: ArgSpec[]; count: number } }
  save_example: {
    params: { id: string; code: string }
    result: { status: 'saved'; id: string; json_file: string | null; path: string }
  }
  run_example: { params: RunExampleParams; result: { run_id: string } }
  stop_run: { params: { run_id: string }; result: { status: 'terminating' | 'pending_terminate'; run_id: string } }
  upload_asset: {
    params: UploadAssetParams
    result: { status: 'uploaded'; filename: string; size: number; path: string; assets: AssetInfo[] }
  }
  list_assets: { params: { id: string }; result: { assets: AssetInfo[] } }
  delete_asset: { params: { id: string; filename: string }; result: { deleted: string; assets: AssetInfo[] } }
  scan_import_source: {
    params: { source_path: string }
    result: { total: number; files: ImportPreviewFile[]; skipped: { file: string; reason: string }[] }
  }
  import_examples: {
    params: { source_path: string; name?: string }
    result: { imported: number; skipped: { file: string; reason: string }[]; collection: string | null; total?: number }
  }
  delete_example: { params: { id: string }; result: { deleted: string; total: number } }
  explain_code: {
    params: { code: string; file_name?: string; context?: string; run_id?: string }
    result: { run_id: string; status?: 'error'; error?: string }
  }
  stop_ai: { params: { run_id: string }; result: { status: 'cancelled'; run_id: string } }
  // A6：存储治理（设置中心「存储」分区）
  storage_report: { params: void; result: StorageReport }
  clean_workspace: { params: { mode: 'clean' | 'all' }; result: { removed: number; kept: number; freed_bytes: number } }
  reclaim_legacy_cache: { params: void; result: { removed: number; freed_bytes: number } }
  // A6：编辑历史（可恢复编辑）
  list_versions: { params: { id: string }; result: { id: string; versions: VersionInfo[] } }
  read_version: { params: { id: string; ts: string }; result: { id: string; ts: string; code: string } }
  restore_version: { params: { id: string; ts: string }; result: { id: string; restored: string } }
  // A6：缺依赖修复（失败恢复）
  install_example_deps: {
    params: { id: string }
    result: { installed: string[]; failed: string[]; packages: string[] }
  }
}

/** 编译期穷尽检查：RPC_METHODS 与 RpcContract 的键必须互相覆盖。 */
type _MethodsCoverContract = RpcMethod extends keyof RpcContract ? true : never
type _ContractCoverMethods = keyof RpcContract extends RpcMethod ? true : never
export type _RpcContractExhaustive = [_MethodsCoverContract, _ContractCoverMethods]

// ---------------------------------------------------------------------------
// 通知负载
// ---------------------------------------------------------------------------

export interface RunOutputEvent {
  run_id: string
  text: string
}
export interface RunFinishedEvent {
  run_id: string
  exit_code: number
}
export interface RunImagesEvent {
  run_id: string
  /** 本次运行新生成图片的 file:// URL 列表（sidecar 扫工作区得出，按修改时间倒序） */
  images: string[]
}
export interface AiExplainChunkEvent {
  run_id: string
  text: string
}
export interface AiExplainDoneEvent {
  run_id: string
  full_text: string
  model: string
  tokens?: number
}
export interface AiExplainErrorEvent {
  run_id: string
  error: string
}
export interface SidecarStatusEvent {
  ready: boolean
  code?: number | null
  crashed?: boolean
  autoRestartDisabled?: boolean
}

// ---------------------------------------------------------------------------
// IPC 命名空间负载（非 JSON-RPC：主进程本地能力）
// ---------------------------------------------------------------------------

export interface AppInfo {
  name: string
  version: string
  electron: string
}
export interface OpenLogResult {
  ok: boolean
  path: string
  error?: string
}
export interface AiSettingsView {
  apiKey: string
  hasKey: boolean
  model: string
  baseUrl: string
  acknowledged: boolean
}
export interface SaveTextResult {
  canceled: boolean
  savedTo?: string
}
export interface DownloadResult {
  canceled?: boolean
  savedTo?: string
  error?: string
}
export interface PickDirectoryResult {
  canceled: boolean
  path?: string
}
export interface MaximizedEvent {
  maximized: boolean
}
