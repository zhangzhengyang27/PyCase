// Electron 主进程：管理窗口、spawn Python sidecar、桥接 IPC。

import { app, BrowserWindow, ipcMain, dialog, Menu, shell, type MenuItemConstructorOptions } from 'electron'
import { spawn, type ChildProcess } from 'node:child_process'
import path from 'node:path'
import fs from 'node:fs'
import { StringDecoder } from 'node:string_decoder'
import { fileURLToPath } from 'node:url'

// 协议通知名表（跨语言单一来源）：sidecar → 渲染层的通知转发由它驱动。
// 曾因主进程手写白名单漏掉 env_progress（protocol.json/ts/server 三处都对，
// 唯独这第四份副本漂移），tests/test_guard_protocol.py 的 G7 护栏钉死接线。
import { NOTIFICATIONS } from '../../../shared/protocol'
import { resolveDataDir } from '../../../shared/paths'
import type { SmokeContext } from './smoke'

// ---------------------------------------------------------------------------
// 路径解析
// ---------------------------------------------------------------------------
// 性能预算（M6-2）计时锚点：模块加载即进程起点（早于 app ready / 建窗 / 拉起 sidecar）
const PROCESS_STARTED_AT = Date.now()
let sidecarReadyAt = 0
let firstListRenderedAt = 0

const IS_PACKAGED = app.isPackaged
const __dirname = path.dirname(fileURLToPath(import.meta.url))

let APP_DIR: string
if (IS_PACKAGED) {
  // 打包模式：数据文件（json_examples）在 resources 目录下
  APP_DIR = process.resourcesPath
} else {
  // 开发模式：从 package.json 所在目录（electron/）向上推导到项目根
  // app.getAppPath() 返回 package.json 所在目录，不随构建产物位置变化
  const ELECTRON_DIR = app.getAppPath()
  const PROTOTYPE_DIR = path.dirname(ELECTRON_DIR)
  APP_DIR = path.dirname(PROTOTYPE_DIR)
}

const SIDECAR_SCRIPT: string | null = IS_PACKAGED
  ? null // 打包模式下不使用源码脚本
  : path.join(APP_DIR, 'electron-prototype', 'sidecar', 'server.py')

interface SidecarCommand {
  command: string
  args: string[]
}

// 解析 sidecar 启动命令：
//   开发模式 → python3 server.py
//   打包模式 → 直接运行 PyInstaller 产物（sidecar 可执行文件）
function resolveSidecarCommand(): SidecarCommand {
  // 环境变量覆盖（调试用）
  if (process.env.SIDECAR_PATH && fs.existsSync(process.env.SIDECAR_PATH)) {
    return { command: process.env.SIDECAR_PATH, args: [] }
  }

  if (IS_PACKAGED) {
    // 打包后 sidecar 可执行文件在 resources 目录下
    const ext = process.platform === 'win32' ? '.exe' : ''
    const bundled = path.join(process.resourcesPath, 'sidecar', `sidecar${ext}`)
    if (fs.existsSync(bundled)) {
      return { command: bundled, args: [] }
    }
    // 兜底：尝试在 resourcesPath 根目录
    const rootSidecar = path.join(process.resourcesPath, `sidecar${ext}`)
    if (fs.existsSync(rootSidecar)) {
      return { command: rootSidecar, args: [] }
    }
    // 打包模式缺失 sidecar 时不能回退到源码模式（SIDECAR_SCRIPT 为 null，
    // spawn(python3, [null]) 会同步抛 TypeError 导致应用无窗口静默挂起）
    throw new Error(`未找到打包的 sidecar 可执行文件（${process.resourcesPath}/sidecar）`)
  }

  // 开发模式：优先用项目共享 venv 的 Python 启动 sidecar（与示例运行环境一致），
  // venv 尚未创建时回退 python3（sidecar 首次运行示例时会自动创建 .venv）
  const venvPython = path.join(
    APP_DIR,
    '.venv',
    process.platform === 'win32' ? path.join('Scripts', 'python.exe') : path.join('bin', 'python')
  )
  const pythonExe = process.env.PYTHON_EXECUTABLE || (fs.existsSync(venvPython) ? venvPython : 'python3')
  return { command: pythonExe, args: [SIDECAR_SCRIPT as string] }
}

// ---------------------------------------------------------------------------
// Sidecar 管理
// ---------------------------------------------------------------------------
interface PendingRequest {
  resolve: (value: unknown) => void
  reject: (reason?: unknown) => void
  // 超时定时器随请求登记：响应/崩溃路径统一摘除——此前从不 clearTimeout，
  // 高频调用下 120s 内累积大量存活定时器（审计 C4）
  timer: NodeJS.Timeout
}

let sidecarProcess: ChildProcess | null = null
let requestId = 0
const pendingRequests = new Map<number, PendingRequest>()
let mainWindow: BrowserWindow | null = null
let sidecarReady = false
const readyQueue: string[] = [] // sidecar 就绪前缓存的消息
// sidecar 崩溃自动重启：手动停止不触发重启；5 分钟内崩溃超 3 次则熔断
let sidecarManuallyStopped = false
const sidecarCrashTimestamps: number[] = []
const SIDECAR_CRASH_WINDOW_MS = 5 * 60 * 1000
const SIDECAR_CRASH_THRESHOLD = 3
const SIDECAR_RESTART_DELAY_MS = 2000

// 事件广播：sidecar 通知与状态需要到达所有渲染窗口（迁移期旧窗口与
// Vue 预览窗口并存，运行输出/就绪状态必须双窗可见）
function broadcast(channel: string, payload: unknown): void {
  for (const win of BrowserWindow.getAllWindows()) {
    if (!win.isDestroyed()) {
      win.webContents.send(channel, payload)
    }
  }
}

function spawnSidecar(): void {
  let command: string
  let args: string[]
  try {
    ;({ command, args } = resolveSidecarCommand())
  } catch (err) {
    // 打包产物不完整：明确告知用户而不是无窗口静默挂起
    dialog.showErrorBox('Sidecar 缺失', `应用组件不完整，无法启动：\n${(err as Error).message}`)
    app.exit(1)
    return
  }
  console.log(`[sidecar] launching: ${command} ${args.join(' ')}`)
  console.log(`[sidecar] mode: ${IS_PACKAGED ? 'packaged' : 'development'}`)

  let proc: ChildProcess
  try {
    proc = spawn(command, args, {
      cwd: APP_DIR,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1',
        // Windows 下管道默认 ANSI 代码页（如 cp936），sidecar 输出中文/emoji
        // 会触发 UnicodeEncodeError；强制 UTF-8 与 JSON-RPC 协议一致
        PYTHONIOENCODING: 'utf-8',
        // 仅打包模式注入可写数据根（venv/示例缓存/运行输出放 userData）：
        // 打包后 Resources 只读；开发模式保持仓库根 .venv 与缓存（README 约定的共享环境）
        ...(IS_PACKAGED ? { DESKTOP_APP_DATA_DIR: app.getPath('userData') } : {}),
        // 走查/CI 上预置运行解释器模式（sidecar 启动即读，避免新机器上白跑一遍共享 venv 引导）
        ...(process.env.SMOKE_RUN_ENV ? { PYCASE_RUN_ENV: process.env.SMOKE_RUN_ENV } : {})
      }
    })
  } catch (err) {
    console.error('[sidecar] spawn 失败:', err)
    return
  }
  sidecarProcess = proc

  const decoder = new StringDecoder('utf-8')
  let stdoutBuffer = ''
  // 用 StringDecoder 在 Buffer 边界解码：直接对 chunk toString 会把跨块的
  // 多字节 UTF-8 字符（如中文）切成 U+FFFD 乱码
  proc.stdout?.on('data', (data: Buffer) => {
    stdoutBuffer += decoder.write(data)
    const lines = stdoutBuffer.split('\n')
    stdoutBuffer = lines.pop() as string // 保留不完整的行
    for (const line of lines) {
      if (line.trim()) {
        handleSidecarMessage(line)
      }
    }
  })

  proc.stderr?.on('data', (data: Buffer) => {
    console.error('[sidecar stderr]', data.toString())
  })

  proc.on('close', (code: number | null) => {
    console.log(`[sidecar] exited with code ${code}`)
    // 引用比较：sidecar:restart 会先 kill 旧进程再 spawn 新进程，旧进程的
    // close 事件晚于新进程赋值到达，不能误清新进程的引用/就绪状态
    const isCurrent = sidecarProcess === proc
    if (isCurrent) {
      sidecarProcess = null
      sidecarReady = false
      // 拒绝所有挂起的请求（定时器一并摘除），并丢弃 ready 缓存——
      // 队列里的是发给**这个**已死进程的消息，新进程就绪后原样重放会
      // 以 id 失配被丢弃，副作用却在重启后的进程上真实执行了一次（审计 C5）
      for (const [id, req] of pendingRequests) {
        const err = new Error('sidecar 进程已退出') as Error & { code?: number }
        err.code = -32001 // 自定义：sidecar 不可用（渲染层据此提示重启而不是重试）
        clearTimeout(req.timer)
        req.reject(err)
        pendingRequests.delete(id)
      }
      readyQueue.length = 0
      broadcast('sidecar:status', { ready: false, code })
    }
    // 手动停止（sidecar:restart）不触发自动重启
    if (sidecarManuallyStopped) {
      sidecarManuallyStopped = false
      return
    }
    if (!isCurrent) return // 陈旧进程的退出事件：新进程已在运行
    // 应用退出阶段不重启
    if (appWithQuitFlag.isQuitting) return
    // 崩溃熔断：5 分钟内崩溃超 3 次则停止自动重启，避免崩溃循环
    const now = Date.now()
    sidecarCrashTimestamps.push(now)
    while (sidecarCrashTimestamps.length && now - sidecarCrashTimestamps[0] > SIDECAR_CRASH_WINDOW_MS) {
      sidecarCrashTimestamps.shift()
    }
    if (sidecarCrashTimestamps.length >= SIDECAR_CRASH_THRESHOLD) {
      console.error(`[sidecar] 5 分钟内崩溃 ${sidecarCrashTimestamps.length} 次，已停止自动重启，请手动重启应用`)
      broadcast('sidecar:status', { ready: false, code, crashed: true, autoRestartDisabled: true })
      return
    }
    // 退避后自动重启
    console.log(
      `[sidecar] ${SIDECAR_RESTART_DELAY_MS}ms 后自动重启（本次窗口内崩溃 ${sidecarCrashTimestamps.length} 次）`
    )
    setTimeout(() => {
      if (!sidecarProcess && !appWithQuitFlag.isQuitting) spawnSidecar()
    }, SIDECAR_RESTART_DELAY_MS)
  })

  proc.on('error', (err: Error) => {
    console.error('[sidecar] spawn error:', err)
  })
}

interface SidecarMessage {
  id?: number
  method?: string
  params?: Record<string, unknown>
  result?: unknown
  error?: { code?: number; message?: string }
}

function handleSidecarMessage(line: string): void {
  let msg: SidecarMessage
  try {
    msg = JSON.parse(line)
  } catch {
    console.error('[sidecar] JSON parse error:', line.slice(0, 200))
    return
  }

  // 通知（无 id）
  if (msg.id === undefined || msg.id === null) {
    if (msg.method === 'sidecar_ready') {
      sidecarReady = true
      console.log('[sidecar] ready')
      if (!sidecarReadyAt) sidecarReadyAt = Date.now()
      broadcast('sidecar:status', { ready: true })
      // 发送缓存的消息
      while (readyQueue.length > 0) {
        const m = readyQueue.shift() as string
        sidecarProcess?.stdin?.write(m + '\n')
      }
    } else if (msg.method && (NOTIFICATIONS as readonly string[]).includes(msg.method)) {
      // 转发到渲染进程（env_progress 等由名表驱动，不手写白名单）
      broadcast(`sidecar:${msg.method}`, msg.params)
    }
    return
  }

  // 响应（有 id）
  const req = pendingRequests.get(msg.id)
  if (req) {
    pendingRequests.delete(msg.id)
    clearTimeout(req.timer)
    if (msg.error) {
      // 错误码必须带出去：渲染层要能按类型分支（C4），只留 message 等于把协议信息丢在半路
      const err = new Error(msg.error.message || 'sidecar 错误') as Error & { code?: number }
      err.code = typeof msg.error.code === 'number' ? msg.error.code : undefined
      req.reject(err)
    } else {
      req.resolve(msg.result)
    }
  }
}

function callSidecar(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const id = ++requestId
    const msg = JSON.stringify({ jsonrpc: '2.0', id, method, params })

    if (!sidecarProcess) {
      const err = new Error('sidecar 未启动') as Error & { code?: number }
      err.code = -32001
      reject(err)
      return
    }

    // 超时保护：预算按方法区分——install_example_deps 逐包分钟级（venv_manager
    // 单包 BOOTSTRAP 就有 600s 预算），120s 必然主进程先超时而 sidecar 仍在锁内
    // 安装，用户重试只会继续排队（审计 C4）
    const timeoutMs = method === 'install_example_deps' ? 900000 : 120000
    const timer = setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id)
        const err = new Error(`请求超时: ${method}`) as Error & { code?: number }
        err.code = -32002 // 自定义：请求超时
        reject(err)
      }
    }, timeoutMs)

    pendingRequests.set(id, { resolve, reject, timer })

    if (sidecarReady) {
      sidecarProcess.stdin?.write(msg + '\n')
    } else {
      readyQueue.push(msg)
    }
  })
}

// ---------------------------------------------------------------------------
// 窗口
// ---------------------------------------------------------------------------
function createWindow(): void {
  const isMac = process.platform === 'darwin'
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'Python 示例管理器',
    // 平台层窗口装饰（A1 §3.1）：
    // - macOS：隐藏系统标题栏，红绿灯嵌入侧栏头区（lead 72px 留白 = 12px 起点 + 三灯 52px + 8px 间隙），
    //   窗口材质走 vibrancy 'sidebar'（侧栏 --bg-sidebar 半透明叠系统毛玻璃）；
    // - Windows：frameless 自绘标题栏（32px + 右上 46×32 三键），窗口底不透明
    ...(isMac
      ? {
          titleBarStyle: 'hiddenInset' as const,
          trafficLightPosition: { x: 12, y: 16 },
          vibrancy: 'sidebar' as const,
          visualEffectState: 'active' as const,
          backgroundColor: '#00000000'
        }
      : { frame: false }),
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  })

  // 拖拽文件/链接到窗口或 window.open 都可能触发导航，导航后的页面会经
  // preload 重新获得完整的特权 API（运行示例、写文件），必须拦截。
  // 白名单 = 应用自身页面：打包态把 file URL 解回路径、只放行 renderer 产物目录
  // （直接放行整个 file:// scheme 曾让拖入窗口的任意本地 HTML 拿到全部特权 API，
  // 审计 C2）；开发态只放行 dev server。setWindowOpenHandler 堵的是 window.open，
  // 堵不了这条。
  const ownPageDir = path.join(__dirname, '../renderer')
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const devUrl = process.env.ELECTRON_RENDERER_URL
    if (devUrl && url.startsWith(devUrl)) return
    if (!devUrl && url.startsWith('file://')) {
      try {
        if (fileURLToPath(url).startsWith(ownPageDir + path.sep)) return
      } catch {
        // 不是合法 file URL（如带 host 的 file://remote/…），按拦截处理
      }
    }
    event.preventDefault()
  })
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))

  // 最大化状态回推渲染层：自绘标题栏的最大化/还原按钮图标据此切换
  const pushMaximized = (): void => broadcast('window:maximized', { maximized: mainWindow?.isMaximized() ?? false })
  mainWindow.on('maximize', pushMaximized)
  mainWindow.on('unmaximize', pushMaximized)
  mainWindow.on('enter-full-screen', pushMaximized)
  mainWindow.on('leave-full-screen', pushMaximized)

  // 开发模式加载 vite dev server，打包模式加载构建产物
  // 冒烟/E2E 模式给入口加 ?smoke=1：渲染层据此注入 window.__app 测试钩子
  const testMode = !!(process.env.SMOKE_TEST || process.env.E2E_TEST)
  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL + (testMode ? '?smoke=1' : ''))
  } else {
    mainWindow.loadFile(
      path.join(__dirname, '../renderer/index.html'),
      testMode ? { query: { smoke: '1' } } : undefined
    )
  }

  // 仅开发模式自动打开 DevTools（打包给用户的正式版不应弹出）；
  // NO_DEVTOOLS=1 供走查/截图用：同一份未打包代码，但不弹面板窗口
  if (!IS_PACKAGED && !process.env.SMOKE_TEST && !process.env.NO_DEVTOOLS) {
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  }
}

// ---------------------------------------------------------------------------
// IPC 处理：窗口控制（Windows frameless 自绘标题栏三键；macOS 走系统红绿灯）
// ---------------------------------------------------------------------------
function senderWindow(event: { sender: Electron.WebContents }): BrowserWindow | null {
  return BrowserWindow.fromWebContents(event.sender)
}

ipcMain.handle('window:minimize', (event) => {
  senderWindow(event)?.minimize()
})
ipcMain.handle('window:toggleMaximize', (event) => {
  const win = senderWindow(event)
  if (!win) return false
  if (win.isMaximized()) win.unmaximize()
  else win.maximize()
  return win.isMaximized()
})
ipcMain.handle('window:close', (event) => {
  senderWindow(event)?.close()
})
ipcMain.handle('window:isMaximized', (event) => senderWindow(event)?.isMaximized() ?? false)

// ---------------------------------------------------------------------------
// IPC 处理：应用与环境信息（帮助面板「环境信息」段、首启页「查看准备日志」）
// ---------------------------------------------------------------------------
ipcMain.handle('app:info', () => ({
  name: app.name,
  version: app.getVersion(),
  electron: process.versions.electron
}))

ipcMain.handle('app:openLog', async () => {
  // 日志由 sidecar 写在 <DATA_DIR>/logs/sidecar.log。DATA_DIR 口径经 shared/paths
  // 与 spawn 注入的 DESKTOP_APP_DATA_DIR 对齐（打包 = userData，开发 = 仓库根）——
  // 不能读主进程自己的 env：该变量只注入给 sidecar 子进程，两种模式都拿不到
  const dir = resolveDataDir({ isPackaged: IS_PACKAGED, userDataPath: app.getPath('userData'), repoRoot: APP_DIR })
  const logPath = path.join(dir, 'logs', 'sidecar.log')
  const err = await shell.openPath(logPath)
  return err ? { ok: false, error: `无法打开日志：${err}`, path: logPath } : { ok: true, path: logPath }
})

// ---------------------------------------------------------------------------
// IPC 处理：渲染进程 -> sidecar
// ---------------------------------------------------------------------------
ipcMain.handle('sidecar:ping', () => callSidecar('ping'))
ipcMain.handle('sidecar:envStatus', () => callSidecar('env_status'))
ipcMain.handle('sidecar:setRunEnv', (_e, mode: string) => callSidecar('set_run_env', { mode }))
ipcMain.handle('sidecar:searchExamples', (_e, query: string, limit?: number) =>
  callSidecar('search_examples', { query, limit })
)
ipcMain.handle('sidecar:listExamples', () => callSidecar('list_examples'))
ipcMain.handle('sidecar:getExample', (_e, id: string) => callSidecar('get_example', { id }))
ipcMain.handle('sidecar:parseArgs', (_e, id: string) => callSidecar('parse_args', { id }))
ipcMain.handle('sidecar:saveExample', (_e, params: { code?: string }) => {
  if (!params || typeof params !== 'object') throw new Error('saveExample: 参数必须是对象')
  if (typeof params.code !== 'string') throw new Error('saveExample: code 必须是字符串')
  if (params.code.length > 500 * 1024) throw new Error('saveExample: code 超过 500KB 限制')
  return callSidecar('save_example', params)
})
ipcMain.handle('sidecar:runExample', (_e, params: Record<string, unknown>) => callSidecar('run_example', params))
ipcMain.handle('sidecar:stopRun', (_e, runId: string) => callSidecar('stop_run', { run_id: runId }))
ipcMain.handle('sidecar:uploadAsset', (_e, params: Record<string, unknown>) => {
  // base64 大小限制：sidecar stdin 单行上限 128MB，超限会直接打崩 sidecar
  if (!params || typeof params.data !== 'string' || params.data.length > 20 * 1024 * 1024) {
    throw new Error('uploadAsset: data 缺失或超过 20MB 限制')
  }
  return callSidecar('upload_asset', params)
})
ipcMain.handle('sidecar:listAssets', (_e, id: string) => callSidecar('list_assets', { id }))
ipcMain.handle('sidecar:deleteAsset', (_e, params: Record<string, unknown>) => callSidecar('delete_asset', params))

// ---------------------------------------------------------------------------
// 用户示例集合（导入向导 / 删除管理）：目录选择 + sidecar RPC 转发
// ---------------------------------------------------------------------------
ipcMain.handle('file:pickDirectory', async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  const { canceled, filePaths } = await dialog.showOpenDialog(win!, {
    title: '选择要导入的示例目录',
    properties: ['openDirectory']
  })
  return canceled || filePaths.length === 0 ? { canceled: true } : { canceled: false, path: filePaths[0] }
})
ipcMain.handle('sidecar:scanExamples', (_e, params: { source_path?: string }) => {
  if (!params || typeof params.source_path !== 'string' || !params.source_path) {
    throw new Error('scanExamples: 缺少 source_path')
  }
  return callSidecar('scan_import_source', { source_path: params.source_path })
})
ipcMain.handle('sidecar:importExamples', (_e, params: { source_path?: string; name?: string }) => {
  if (!params || typeof params.source_path !== 'string' || !params.source_path) {
    throw new Error('importExamples: 缺少 source_path')
  }
  if (params.name !== undefined && typeof params.name !== 'string') {
    throw new Error('importExamples: name 必须是字符串')
  }
  return callSidecar('import_examples', { source_path: params.source_path, name: params.name })
})
ipcMain.handle('sidecar:deleteExample', (_e, params: { id?: string }) => {
  if (!params || typeof params.id !== 'string' || !params.id) {
    throw new Error('deleteExample: 缺少 id')
  }
  return callSidecar('delete_example', { id: params.id })
})

// ---------------------------------------------------------------------------
// AI 代码解释（DeepSeek）：key 从 userData 读取后注入 sidecar，不进前端/git/日志
// ---------------------------------------------------------------------------
const AI_SETTINGS_FIELDS = ['apiKey', 'model', 'baseUrl', 'acknowledged'] as const

interface AISettings {
  apiKey?: string
  model?: string
  baseUrl?: string
  acknowledged?: boolean
}

ipcMain.handle('ai:getSettings', async () => {
  const data = ((await readStore('aiSettings')) as AISettings) || {}
  return {
    apiKey: data.apiKey ? '********' : '', // 不回传明文 key，前端只显示是否已配置
    hasKey: !!data.apiKey,
    model: data.model || 'deepseek-chat',
    baseUrl: data.baseUrl || 'https://api.deepseek.com',
    acknowledged: !!data.acknowledged
  }
})

// ai:setSettings 的 baseUrl 校验：渲染层被攻破时若无约束，
// 可把 apiKey 重定向到任意服务器窃取 key
function isValidAiBaseUrl(url: string): boolean {
  try {
    const u = new URL(url)
    if (u.protocol === 'https:') return true
    // 本地调试允许 http
    return u.protocol === 'http:' && (u.hostname === 'localhost' || u.hostname === '127.0.0.1')
  } catch {
    return false
  }
}

ipcMain.handle('ai:setSettings', async (_e, patch: Partial<AISettings>) => {
  if (patch.baseUrl !== undefined && patch.baseUrl !== '' && !isValidAiBaseUrl(patch.baseUrl)) {
    throw new Error('ai:setSettings: baseUrl 必须是 https:// 地址（本地调试可用 http://localhost）')
  }
  const cur = ((await readStore('aiSettings')) as AISettings) || {}
  const next: AISettings = { ...cur }
  for (const k of AI_SETTINGS_FIELDS) {
    if (k in patch) (next as Record<string, unknown>)[k] = (patch as Record<string, unknown>)[k]
  }
  // 空字符串 key 视为清除
  if (next.apiKey === '') delete next.apiKey
  await writeStore('aiSettings', next)
  return { ok: true, hasKey: !!next.apiKey }
})

ipcMain.handle('ai:explain', async (_e, { code, file_name }: { code: string; file_name?: string }) => {
  if (typeof code !== 'string') throw new Error('ai:explain: code 必须是字符串')
  if (code.length > 100 * 1024) throw new Error('ai:explain: code 超过 100KB 限制')
  const settings = ((await readStore('aiSettings')) as AISettings) || {}
  if (!settings.apiKey) {
    return { run_id: '', status: 'error', error: 'no_api_key' }
  }
  return callSidecar('explain_code', {
    code,
    file_name: file_name || '',
    api_key: settings.apiKey,
    base_url: settings.baseUrl || 'https://api.deepseek.com',
    model: settings.model || 'deepseek-chat'
  })
})

ipcMain.handle('ai:stop', (_e, runId: string) => callSidecar('stop_ai', { run_id: runId }))

// 下载运行结果图片：弹出保存对话框，把处理结果复制到用户选择的位置
// 读侧白名单：来源必须位于示例缓存目录内，防止被攻破的渲染层用该接口
// 把任意可读文件（如 ~/.ssh/id_rsa）经另存对话框带出。
// 缓存根有两个候选：打包模式在 userData（DESKTOP_APP_DATA_DIR 注入），开发模式在仓库根
function isInsideExamplesCache(srcPath: string): boolean {
  const roots = [path.join(app.getPath('userData'), '.json_examples_cache'), path.join(APP_DIR, '.json_examples_cache')]
  let real: string
  try {
    real = fs.realpathSync(srcPath)
  } catch {
    return false
  }
  return roots.some((root) => {
    const resolvedRoot = path.resolve(root)
    return real === resolvedRoot || real.startsWith(resolvedRoot + path.sep)
  })
}

ipcMain.handle(
  'file:downloadResultImage',
  async (event, { url, defaultName }: { url: string; defaultName?: string }) => {
    try {
      const srcPath = fileURLToPath(url)
      if (!fs.existsSync(srcPath)) {
        return { error: `文件不存在：${srcPath}` }
      }
      if (!isInsideExamplesCache(srcPath)) {
        return { error: '只允许保存示例运行目录内的文件' }
      }
      const win = BrowserWindow.fromWebContents(event.sender)
      const { canceled, filePath } = await dialog.showSaveDialog(win!, {
        title: '保存处理结果',
        defaultPath: defaultName || path.basename(srcPath)
      })
      if (canceled || !filePath) {
        return { canceled: true }
      }
      await fs.promises.copyFile(srcPath, filePath)
      return { canceled: false, savedTo: filePath }
    } catch (err) {
      return { error: (err as Error).message }
    }
  }
)

// A6：存储治理 / 编辑历史 / 缺依赖修复（薄转发；校验与业务在 sidecar 侧）
ipcMain.handle('sidecar:storageReport', () => callSidecar('storage_report'))
ipcMain.handle('sidecar:cleanWorkspace', (_e, mode: string) => callSidecar('clean_workspace', { mode }))
ipcMain.handle('sidecar:reclaimLegacyCache', () => callSidecar('reclaim_legacy_cache'))
ipcMain.handle('sidecar:listVersions', (_e, id: string) => callSidecar('list_versions', { id }))
ipcMain.handle('sidecar:readVersion', (_e, params: { id: string; ts: string }) => callSidecar('read_version', params))
ipcMain.handle('sidecar:restoreVersion', (_e, params: { id: string; ts: string }) =>
  callSidecar('restore_version', params)
)
ipcMain.handle('sidecar:installExampleDeps', (_e, id: string) => callSidecar('install_example_deps', { id }))

ipcMain.handle('sidecar:restart', async () => {
  if (sidecarProcess) {
    sidecarManuallyStopped = true
    const old = sidecarProcess
    old.kill()
    // 等旧进程真正退出再 spawn 新进程：否则旧进程的 close 事件会在新进程
    // 赋值之后到达，竞态清空新进程引用导致所有调用永久失败
    await new Promise<void>((resolve) => {
      if (old.exitCode !== null || old.signalCode !== null) resolve()
      else {
        const timer = setTimeout(resolve, 3000) // 进程无响应时超时放行
        old.once('close', () => {
          clearTimeout(timer)
          resolve()
        })
      }
    })
  }
  spawnSidecar()
  return { status: 'restarting' }
})

// ---------------------------------------------------------------------------
// 用户数据存储：小 JSON 文件写入 userData（打包后 Resources 只读，禁止写应用目录）
// 白名单约束文件名，防止路径穿越；原子写（tmp + rename）
// ---------------------------------------------------------------------------
// onboarding：首启引导是否已看过（A5.5）；名字即文件名，白名单是唯一写盘入口
const STORE_WHITELIST = new Set([
  'history',
  'favorites',
  'aiSettings',
  'viewPrefs',
  'safetyPrefs',
  'runPrefs',
  'onboarding'
])

function storeFile(name: string): string {
  if (!STORE_WHITELIST.has(name)) throw new Error(`非法的存储名: ${name}`)
  return path.join(app.getPath('userData'), `${name}.json`)
}

function readStore(name: string): unknown {
  try {
    return JSON.parse(fs.readFileSync(storeFile(name), 'utf-8'))
  } catch (err) {
    const e = err as NodeJS.ErrnoException
    if (e.code === 'ENOENT') return null // 文件不存在是正常的，由渲染层兜底
    // JSON 损坏或读取错误：备份损坏文件，避免下次继续失败，用户数据不丢失
    console.error(`[store] ${name}.json 读取失败:`, e.message)
    try {
      const target = storeFile(name)
      if (fs.existsSync(target)) {
        const backup = `${target}.corrupted-${Date.now()}`
        fs.renameSync(target, backup)
        console.error(`[store] 损坏文件已备份到: ${backup}`)
      }
    } catch (backupErr) {
      console.error('[store] 备份损坏文件失败:', (backupErr as Error).message)
    }
    return null
  }
}

function writeStore(name: string, data: unknown): unknown {
  const target = storeFile(name)
  const tmp = `${target}.tmp`
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2), 'utf-8')
  fs.renameSync(tmp, target)
  return data
}

ipcMain.handle('store:get', (_event, name: string) => readStore(name))
ipcMain.handle('store:set', (_event, name: string, data: unknown) => {
  // 输入验证：必须可 JSON 序列化且不超过 1MB，防止循环引用或超大数据导致崩溃
  let serialized: string
  try {
    serialized = JSON.stringify(data)
  } catch (e) {
    throw new Error(`store:set: 数据不可序列化: ${(e as Error).message}`)
  }
  if (serialized.length > 1024 * 1024) {
    throw new Error('store:set: 数据超过 1MB 限制')
  }
  return writeStore(name, data)
})

// 通用文本另存为（运行历史导出 .log 等）
ipcMain.handle(
  'file:saveText',
  async (
    event,
    {
      content,
      defaultName,
      filters
    }: { content?: string; defaultName?: string; filters?: { name: string; extensions: string[] }[] }
  ) => {
    const win = BrowserWindow.fromWebContents(event.sender)
    const { canceled, filePath } = await dialog.showSaveDialog(win!, {
      title: '导出',
      defaultPath: defaultName || 'export.txt',
      filters: filters || [{ name: '文本文件', extensions: ['txt', 'log', 'md', 'json'] }]
    })
    if (canceled || !filePath) return { canceled: true }
    await fs.promises.writeFile(filePath, content ?? '', 'utf-8')
    return { canceled: false, savedTo: filePath }
  }
)

// ---------------------------------------------------------------------------
// 走查上下文工厂：把冒烟/E2E 需要的产品内部状态收拢为一个只读门面（审计 C3）。
// smoke/E2E 本体已拆至 ./smoke.ts，仅在 SMOKE_TEST / E2E_TEST 就位时动态加载，
// 产品 chunk 不再静态承载 1200 行走查索具。
// ---------------------------------------------------------------------------
function makeSmokeContext(): SmokeContext {
  return {
    getWindow: () => mainWindow,
    callSidecar,
    isSidecarReady: () => sidecarReady,
    startedAt: PROCESS_STARTED_AT,
    getSidecarReadyAt: () => sidecarReadyAt,
    getFirstListRenderedAt: () => firstListRenderedAt,
    markFirstListRendered: () => {
      if (!firstListRenderedAt) firstListRenderedAt = Date.now()
    },
    isPackaged: IS_PACKAGED,
    appDir: APP_DIR
  }
}

// ---------------------------------------------------------------------------
// 全局异常兜底：未捕获异常不直接崩溃，记录日志并尝试通知渲染层
// ---------------------------------------------------------------------------
process.on('uncaughtException', (err: Error) => {
  console.error('[main] uncaughtException:', err)
  // 落盘到 <DATA_DIR>/logs/main-error.log：sidecar 有 sidecar.log，主进程崩溃
  // 前若只留 console，用户「查看日志」时没有任何可查痕迹（审计 C7）
  try {
    const logDir = path.join(
      resolveDataDir({ isPackaged: IS_PACKAGED, userDataPath: app.getPath('userData'), repoRoot: APP_DIR }),
      'logs'
    )
    fs.mkdirSync(logDir, { recursive: true })
    fs.appendFileSync(
      path.join(logDir, 'main-error.log'),
      `[${new Date().toISOString()}] uncaughtException\n${err.stack || err.message}\n\n`
    )
  } catch {
    // 日志落盘失败不能盖过异常本身
  }
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('main:error', { message: err.message, stack: err.stack })
    }
  } catch {
    // 忽略通知失败
  }
  // 冒烟模式下未捕获异常视为失败
  if (process.env.SMOKE_TEST) {
    console.error('[smoke] 主进程未捕获异常，判定失败')
    app.exit(1)
  }
})

process.on('unhandledRejection', (reason: unknown) => {
  console.error('[main] unhandledRejection:', reason)
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('main:error', {
        message: reason instanceof Error ? reason.message : String(reason)
      })
    }
  } catch {
    // 忽略通知失败
  }
})

// ---------------------------------------------------------------------------
// 应用菜单：中文标签 + 标准 role（编辑复制粘贴、视图缩放、窗口管理）。
// 不设置则为英文默认菜单，与全中文 UI 割裂；关于面板同样本地化。
// ---------------------------------------------------------------------------
function setupMenu(): void {
  const isMac = process.platform === 'darwin'
  const template: MenuItemConstructorOptions[] = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: 'about' },
              { type: 'separator' },
              { role: 'hide' },
              { role: 'hideOthers' },
              { role: 'unhide' },
              { type: 'separator' },
              { role: 'quit' }
            ]
          } satisfies MenuItemConstructorOptions
        ]
      : []),
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: '窗口',
      submenu: isMac
        ? [{ role: 'minimize' }, { role: 'zoom' }, { type: 'separator' }, { role: 'front' }]
        : [{ role: 'minimize' }, { role: 'close' }]
    }
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

// ---------------------------------------------------------------------------
// 应用生命周期
// ---------------------------------------------------------------------------
app.whenReady().then(() => {
  app.setAboutPanelOptions({
    applicationName: 'Python 示例管理器',
    applicationVersion: app.getVersion(),
    version: process.versions.electron
  })
  setupMenu()
  spawnSidecar()
  createWindow()

  if (process.env.SMOKE_TEST) {
    void import('./smoke').then(({ runSmokeTest }) => runSmokeTest(makeSmokeContext()))
  }

  if (process.env.E2E_TEST) {
    void import('./smoke').then(({ runE2ETest }) => runE2ETest(makeSmokeContext()))
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
    // macOS 关窗后从 Dock 重开：窗口重建的同时恢复 sidecar
    // （此前只重建窗口，sidecar 若已退出则应用不可用）
    if (!sidecarProcess && !appWithQuitFlag.isQuitting) {
      spawnSidecar()
    }
  })
})

// Electron 的 App 类型没有 isQuitting 字段，但退出阶段必须能读到它：
// 此前只被读取从未赋值，退出时 sidecar 被 kill 后 close 事件仍走"崩溃"分支
// 排定 2 秒后重启，可产生僵尸 sidecar
const appWithQuitFlag = app as Electron.App & { isQuitting?: boolean }
app.on('before-quit', () => {
  appWithQuitFlag.isQuitting = true
})

app.on('window-all-closed', () => {
  if (process.platform === 'darwin') {
    // darwin 关窗不退出：sidecar 保持运行——用户随时可能重开窗口，热引擎体验更好。
    // 此前无条件 kill，close 事件 2 秒后又自动重启：无窗口状态下白拉起一个
    // sidecar（审计 C6）。退出统一走 before-quit + 进程退出清理。
    return
  }
  // 非 darwin 关窗 = 退出：sidecar 一并终止（Windows 的 TerminateProcess 不给
  // sidecar 执行清理的机会，属已知取舍；进程组收口在 sidecar 侧 _spawn_isolation_kwargs）
  if (sidecarProcess) {
    sidecarProcess.kill()
  }
  app.quit()
})
