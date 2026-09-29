// Electron 主进程：管理窗口、spawn Python sidecar、桥接 IPC。

import { app, BrowserWindow, ipcMain, dialog, Menu, shell, type MenuItemConstructorOptions } from 'electron'
import { spawn, type ChildProcess } from 'node:child_process'
import path from 'node:path'
import os from 'node:os'
import fs from 'node:fs'
import { StringDecoder } from 'node:string_decoder'
import { fileURLToPath } from 'node:url'

// ---------------------------------------------------------------------------
// 路径解析
// ---------------------------------------------------------------------------
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
  const pythonExe =
    process.env.PYTHON_EXECUTABLE ||
    (fs.existsSync(venvPython) ? venvPython : 'python3')
  return { command: pythonExe, args: [SIDECAR_SCRIPT as string] }
}

// ---------------------------------------------------------------------------
// Sidecar 管理
// ---------------------------------------------------------------------------
interface PendingRequest {
  resolve: (value: unknown) => void
  reject: (reason?: unknown) => void
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
        ...(IS_PACKAGED ? { DESKTOP_APP_DATA_DIR: app.getPath('userData') } : {})
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
      // 拒绝所有挂起的请求
      for (const [id, req] of pendingRequests) {
        req.reject(new Error('sidecar 进程已退出'))
        pendingRequests.delete(id)
      }
      broadcast('sidecar:status', { ready: false, code })
    }
    // 手动停止（sidecar:restart）不触发自动重启
    if (sidecarManuallyStopped) {
      sidecarManuallyStopped = false
      return
    }
    if (!isCurrent) return // 陈旧进程的退出事件：新进程已在运行
    // 应用退出阶段不重启
    if ((app as any).isQuitting) return
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
    console.log(`[sidecar] ${SIDECAR_RESTART_DELAY_MS}ms 后自动重启（本次窗口内崩溃 ${sidecarCrashTimestamps.length} 次）`)
    setTimeout(() => {
      if (!sidecarProcess && !(app as any).isQuitting) spawnSidecar()
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
  error?: { message?: string }
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
      broadcast('sidecar:status', { ready: true })
      // 发送缓存的消息
      while (readyQueue.length > 0) {
        const m = readyQueue.shift() as string
        sidecarProcess?.stdin?.write(m + '\n')
      }
    } else if (msg.method === 'run_output' || msg.method === 'run_finished' || msg.method === 'run_images' ||
               msg.method === 'ai_explain_chunk' || msg.method === 'ai_explain_done' || msg.method === 'ai_explain_error') {
      // 转发到渲染进程
      broadcast(`sidecar:${msg.method}`, msg.params)
    }
    return
  }

  // 响应（有 id）
  const req = pendingRequests.get(msg.id)
  if (req) {
    pendingRequests.delete(msg.id)
    if (msg.error) {
      req.reject(new Error(msg.error.message || 'sidecar 错误'))
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
      reject(new Error('sidecar 未启动'))
      return
    }

    pendingRequests.set(id, { resolve, reject })

    if (sidecarReady) {
      sidecarProcess.stdin?.write(msg + '\n')
    } else {
      readyQueue.push(msg)
    }

    // 超时保护
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id)
        reject(new Error(`请求超时: ${method}`))
      }
    }, 120000)
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
  // preload 重新获得完整的特权 API（运行示例、写文件），必须拦截
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const devUrl = process.env.ELECTRON_RENDERER_URL
    if (url.startsWith('file://') || (devUrl && url.startsWith(devUrl))) return
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
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'), testMode ? { query: { smoke: '1' } } : undefined)
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
  // 日志由 sidecar 写在 <DATA_DIR>/logs/sidecar.log（DATA_DIR 由 DESKTOP_APP_DATA_DIR 决定）
  const dir = process.env.DESKTOP_APP_DATA_DIR || app.getAppPath()
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
    if (k in patch) next[k] = patch[k] as any
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

ipcMain.handle('file:downloadResultImage', async (event, { url, defaultName }: { url: string; defaultName?: string }) => {
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
})

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
const STORE_WHITELIST = new Set(['history', 'favorites', 'aiSettings', 'viewPrefs', 'safetyPrefs', 'runPrefs', 'onboarding'])

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
ipcMain.handle('file:saveText', async (event, { content, defaultName, filters }: { content?: string; defaultName?: string; filters?: { name: string; extensions: string[] }[] }) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  const { canceled, filePath } = await dialog.showSaveDialog(win!, {
    title: '导出',
    defaultPath: defaultName || 'export.txt',
    filters: filters || [{ name: '文本文件', extensions: ['txt', 'log', 'md', 'json'] }]
  })
  if (canceled || !filePath) return { canceled: true }
  await fs.promises.writeFile(filePath, content ?? '', 'utf-8')
  return { canceled: false, savedTo: filePath }
})

// ---------------------------------------------------------------------------
// 冒烟自测：SMOKE_TEST=1 时启动后自动验证关键链路并退出（退出码 0/1）
// 覆盖：sidecar ready → ping → listExamples 非空 → 渲染进程无 console error
// ---------------------------------------------------------------------------
function runSmokeTest(): void {
  const failures: string[] = []
  // 冒烟总超时：默认 180s，可用 SMOKE_TIMEOUT_MS 覆盖。
  // 链路耗时随示例量增长，本机实测（1496 个示例）：首次 list_examples ≈17s、
  // import ≈13s、每次 delete ≈13s——仅「导入/删除」三步就要 40s+，加上
  // 渲染层加载与末尾 8s 观察窗，原先的 45s 在原样跑通之前就会超时。
  const timeoutMs = Number(process.env.SMOKE_TIMEOUT_MS) || 180000
  // 记录当前阶段：超时时能直接看出卡在哪一步，而不是只报一句「未完成」
  let step = 'sidecar 启动'
  const deadline = setTimeout(() => {
    console.error(`[smoke] ${Math.round(timeoutMs / 1000)}s 内未完成（卡在：${step}），判定失败`)
    app.exit(1)
  }, timeoutMs)

  mainWindow?.webContents.on('console-message', (_event, level, message) => {
    if (level === 3) failures.push(`renderer console error: ${message}`)
  })
  mainWindow?.webContents.on('render-process-gone', (_e, details) => {
    console.error('[smoke] 渲染进程崩溃:', details.reason)
    app.exit(1)
  })

  const waitFor = async (
    predicate: () => boolean | Promise<boolean>,
    label: string,
    timeoutMs = 20000
  ): Promise<void> => {
    const start = Date.now()
    while (!(await predicate())) {
      if (Date.now() - start > timeoutMs) throw new Error(`等待超时: ${label}`)
      await new Promise((r) => setTimeout(r, 300))
    }
  }

  void (async () => {
    try {
      step = 'sidecar ready'
      await waitFor(() => sidecarReady, 'sidecar ready')
      const ping = await callSidecar('ping') as { status?: string }
      if (!ping || ping.status !== 'ok') throw new Error('ping 返回异常')
      step = 'list_examples'
      const list = await callSidecar('list_examples') as { total?: number; tree?: { children?: unknown[] } }
      if (!list || !list.total || list.total < 100) throw new Error(`示例数量异常: ${list && list.total}`)
      if (!list.tree || !list.tree.children || list.tree.children.length === 0) throw new Error('目录树为空')
      console.log(`[smoke] sidecar 正常，示例 ${list.total} 个，集合 ${list.tree.children.length} 个`)
      // 等渲染进程（Vue）完成 loadExamples
      step = 'Vue 应用加载示例'
      await waitFor(async () => {
        const n = await mainWindow!.webContents.executeJavaScript('window.__app ? window.__app.examples().length : 0') as number
        return n > 100
      }, 'Vue 应用加载示例')
      // 首启页在首次运行时是全屏遮罩，会盖住后续截图与点击：先收起（其自身的走查放到最后）
      await mainWindow!.webContents.executeJavaScript('window.__app && window.__app.dismissOnboarding && window.__app.dismissOnboarding()')
      // 壳与导航走查（A2）：在真实窗口里量三层绑定与平台几何，而不是看截图
      step = '壳与导航走查'
      const shell = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const out = {};
        const root = document.documentElement;
        const cs = getComputedStyle(root);
        const px = (v) => parseFloat(v);
        const isWin = root.getAttribute('data-platform') === 'win';
        // 1) 三层绑定属性：平台由 preload 按 process.platform 写入，强调色默认 system
        out.platform = root.getAttribute('data-platform');
        out.accent = root.getAttribute('data-accent');
        out.theme = root.getAttribute('data-theme');
        // 2) 平台几何：侧栏宽 / 行高 / 标题栏高 / 状态栏高 必须等于平台层令牌
        const nav = document.querySelector('nav.sidebar');
        const head = document.querySelector('nav.sidebar .side-head');
        const row = document.querySelector('nav.sidebar .navitem');
        const status = document.querySelector('footer.statusbar');
        if (!nav || !head || !row || !status) return { fatal: '壳结构缺失（nav.sidebar/.side-head/.navitem/footer.statusbar）' };
        out.sidebarW = Math.round(nav.getBoundingClientRect().width);
        out.rowH = Math.round(row.getBoundingClientRect().height);
        out.headH = Math.round(head.getBoundingClientRect().height);
        out.statusH = Math.round(status.getBoundingClientRect().height);
        out.expect = {
          sidebarW: px(cs.getPropertyValue('--sidebar-w')),
          rowH: px(cs.getPropertyValue('--row-h')),
          titlebarH: px(cs.getPropertyValue('--titlebar-h')),
          statusH: px(cs.getPropertyValue('--statusbar-h'))
        };
        // 3) 侧栏头区留白 = 平台标题栏前导（mac 72 给红绿灯 / win 12）
        out.headPadLeft = Math.round(px(getComputedStyle(head).paddingLeft));
        out.expectLead = px(cs.getPropertyValue('--titlebar-lead'));
        // 4) 选中语义：mac = 强调填充 + on-accent 文字；win = 中性填充 + 强调条
        const sel = document.querySelector('nav.sidebar .navitem.sel');
        if (!sel) return { fatal: '无选中导航项（.navitem.sel）' };
        const selCs = getComputedStyle(sel);
        out.selBg = selCs.backgroundColor;
        out.selColor = selCs.color;
        out.selWeight = selCs.fontWeight;
        out.accentBarDisplay = getComputedStyle(sel.querySelector('.accent-bar')).display;
        out.navIndicator = cs.getPropertyValue('--nav-indicator').trim();
        // 5) 侧栏材质：macOS 半透明（叠系统毛玻璃）vs win 实色
        out.sidebarBg = getComputedStyle(nav).backgroundColor;
        // 6) Windows 自绘标题栏：mac 隐藏、win 显示且三键 46×32
        const tb = document.querySelector('.titlebar-win');
        out.titlebarDisplay = tb ? getComputedStyle(tb).display : 'MISSING';
        if (isWin && tb) {
          const btns = Array.from(tb.querySelectorAll('.caption-btn'));
          out.caption = btns.map((b) => Math.round(b.getBoundingClientRect().width) + 'x' + Math.round(b.getBoundingClientRect().height));
          out.captionCount = btns.length;
        }
        // 7) 焦点环：键盘焦点样式取自平台令牌（不硬编码）
        out.focusShadow = cs.getPropertyValue('--focus-shadow').trim();
        // 7b) 字号基准：根 16px（rem 计工具类的换算基准），正文 = --fs-body。
        //     两者若相等，说明正文尺寸写进了 html，全部 rem 尺寸会缩水到 13/16
        out.rootFs = px(getComputedStyle(root).fontSize);
        out.bodyFs = px(getComputedStyle(document.body).fontSize);
        out.fsBody = px(cs.getPropertyValue('--fs-body'));
        // 8) 窗口控制：直接 IPC 往返（只测可逆的最大化/还原，不碰最小化与关闭）
        try {
          const before = await window.sidecar.win.isMaximized();
          const toMax = await window.sidecar.win.toggleMaximize();
          await sleep(400);
          const afterEvents = await window.sidecar.win.isMaximized();
          await window.sidecar.win.toggleMaximize();
          await sleep(400);
          const restored = await window.sidecar.win.isMaximized();
          out.winCtl = { before, toMax, afterEvents, restored };
        } catch (e) {
          out.winCtl = { error: String(e) };
        }
        // 9) 标题栏按钮的"点击 → IPC"整条链路（按钮在 mac 下 display:none，但仍在 DOM 中，
        //    可点：证明接线与直接调 IPC 不是两回事）
        try {
          const btns = document.querySelectorAll('.titlebar-win .caption-btn');
          out.captionClickable = btns.length;
          if (btns.length === 3) {
            btns[1].click(); // 最大化/还原
            await sleep(500);
            const afterClick = await window.sidecar.win.isMaximized();
            btns[1].click();
            await sleep(500);
            out.maximizedByClick = afterClick;
            out.restoredByClick = await window.sidecar.win.isMaximized();
          }
        } catch (e) {
          out.captionCtl = { error: String(e) };
        }
        return out;
      })()`) as Record<string, unknown>
      {
        const s = shell as Record<string, unknown>
        if (s.fatal) throw new Error(`壳走查: ${s.fatal}`)
        const exp = s.expect as Record<string, number>
        const near = (a: unknown, b: number, tol = 1): boolean => Math.abs((a as number) - b) <= tol
        const problems: string[] = []
        if (s.platform !== 'mac' && s.platform !== 'win') problems.push(`data-platform=${s.platform}`)
        if (s.accent !== 'system' && s.accent !== 'brand') problems.push(`data-accent=${s.accent}`)
        if (!near(s.sidebarW, exp.sidebarW)) problems.push(`侧栏宽 ${s.sidebarW} != ${exp.sidebarW}`)
        if (!near(s.rowH, exp.rowH)) problems.push(`行高 ${s.rowH} != ${exp.rowH}`)
        if (!near(s.headH, exp.titlebarH)) problems.push(`头区高 ${s.headH} != ${exp.titlebarH}`)
        if (!near(s.statusH, exp.statusH)) problems.push(`状态栏高 ${s.statusH} != ${exp.statusH}`)
        if (!near(s.headPadLeft, s.expectLead as number)) problems.push(`头区留白 ${s.headPadLeft} != ${s.expectLead}`)
        // 选中语义按平台分流：断言"与令牌一致"，而不是断言某个平台的固定色值
        if (s.platform === 'win') {
          if (s.accentBarDisplay === 'none') problems.push('win 选中项缺强调条')
          if (s.navIndicator !== 'block') problems.push(`win --nav-indicator=${s.navIndicator}`)
          if (s.titlebarDisplay === 'none') problems.push('win 自绘标题栏未显示')
          if (s.captionCount !== 3) problems.push(`win 窗口三键数=${s.captionCount}`)
        } else {
          if (s.accentBarDisplay !== 'none') problems.push('mac 选中项出现强调条')
          if (s.navIndicator !== 'none') problems.push(`mac --nav-indicator=${s.navIndicator}`)
          if (s.titlebarDisplay !== 'none') problems.push('mac 自绘标题栏未隐藏')
        }
        const wc = s.winCtl as Record<string, unknown>
        if (wc.error) problems.push(`窗口控制 IPC: ${wc.error}`)
        else if (wc.toMax !== true || wc.afterEvents !== true || wc.restored !== false) {
          problems.push(`窗口控制往返异常: ${JSON.stringify(wc)}`)
        }
        if (!String(s.focusShadow).trim()) problems.push('焦点环令牌为空')
        if (s.rootFs !== 16) problems.push(`根字号 ${s.rootFs}px（rem 基准应为 16px）`)
        if (s.bodyFs !== s.fsBody) problems.push(`正文字号 ${s.bodyFs} != --fs-body ${s.fsBody}`)
        if (s.captionClickable !== 3) problems.push(`标题栏按钮缺失（${s.captionClickable} 个）`)
        else if (s.maximizedByClick !== true || s.restoredByClick !== false) {
          problems.push(`按钮点击链路异常: ${JSON.stringify({ m: s.maximizedByClick, r: s.restoredByClick })}`)
        }
        if (problems.length) throw new Error('壳走查失败: ' + problems.join('; '))
        console.log(`[smoke] 壳走查通过：${s.platform}/${s.theme}/${s.accent} 侧栏 ${s.sidebarW} 行高 ${s.rowH} 标题栏 ${s.headH} 状态栏 ${s.statusH} 选中底 ${s.selBg}`)
      }
      // 画廊/工具箱走查（A3）：在真实窗口里走一遍页面语言——图标来源、字重、状态圆点、分段控件
      step = '画廊页面走查'
      const page = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const root = document.documentElement;
        const isWin = root.getAttribute('data-platform') === 'win';
        const out = {};
        const emojiRe = /[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}]/u;
        // 1) 总览态：分区 + 卡片语言
        out.sections = document.querySelectorAll('main section').length;
        const cards = Array.from(document.querySelectorAll('[role="button"][aria-label$="（详情）"]'));
        out.cards = cards.length;
        if (!cards.length) return { fatal: '画廊总览没有卡片' };
        const card = cards[0];
        const chip = card.querySelector('.chip-ic');
        out.cardChip = !!chip;
        out.cardChipSvg = !!(chip && chip.querySelector('svg'));
        out.cardChipText = chip ? (chip.textContent || '').trim() : 'MISSING';
        // 只查 UI chrome：chip 容器与标题——示例描述/标签属数据，可能自带 emoji，不算 UI 语言
        const chromeText = (el) => Array.from(el.querySelectorAll('.chip-ic, .hue-chip, .font-semibold, .stat-dot, button')).map((n) => n.textContent || '').join('');
        out.cardEmoji = emojiRe.test(chromeText(card));
        out.cardsEmoji = cards.slice(0, 30).some((c) => emojiRe.test(chromeText(c)));
        // 字重：卡片标题必须是 600（v2 只允许 400/500/600）
        const titleEl = card.querySelector('.font-semibold');
        out.cardTitleWeight = titleEl ? getComputedStyle(titleEl).fontWeight : 'MISSING';
        // 全页抽样：卡片内出现的字号/字重白名单（抓非标字重回归）
        const weights = new Set();
        for (const el of cards.slice(0, 12)) {
          for (const n of el.querySelectorAll('*')) weights.add(getComputedStyle(n).fontWeight);
        }
        out.cardWeights = Array.from(weights).sort();
        // 分区头：语义图标 + 无 emoji
        const secHead = document.querySelector('main section .chip-ic');
        out.sectionChipSvg = !!(secHead && secHead.querySelector('svg'));
        const secs = Array.from(document.querySelectorAll('main section'));
        out.sectionEmoji = secs.some((sec) => {
          const head = sec.firstElementChild;
          return head ? emojiRe.test(chromeText(head)) : false;
        });
        // 2) 进浏览态：点「浏览全部」（真实用户路径）
        const browseAll = Array.from(document.querySelectorAll('button')).find((b) => (b.textContent || '').includes('浏览全部'));
        if (!browseAll) return { fatal: '总览页找不到「浏览全部」按钮' };
        browseAll.click();
        await sleep(700);
        // 3) 分段控件：平台语义（mac = 抬起段底 + 主文字；win = 强调文字 + 下划线）
        const seg = document.querySelector('.seg');
        out.seg = !!seg;
        if (seg) {
          const btns = Array.from(seg.querySelectorAll('button'));
          out.segCount = btns.length;
          const active = btns.find((b) => b.getAttribute('aria-pressed') === 'true');
          out.segActive = !!active;
          if (active) {
            const probe = document.createElement('div');
            probe.style.cssText = 'position:absolute;visibility:hidden;background:var(--bg-pressed);color:var(--text-primary)';
            document.body.appendChild(probe);
            const csProbe = getComputedStyle(probe);
            out.expectPressedBg = csProbe.backgroundColor;
            out.expectPrimary = csProbe.color;
            probe.remove();
            const cs2 = getComputedStyle(active);
            out.segActiveBg = cs2.backgroundColor;
            out.segActiveColor = cs2.color;
            const probe2 = document.createElement('div');
            probe2.style.cssText = 'position:absolute;visibility:hidden;color:var(--accent-text)';
            document.body.appendChild(probe2);
            out.expectAccentText = getComputedStyle(probe2).color;
            probe2.remove();
          }
        }
        // 4) 浏览态工具条高度 = --toolbar-h（平台几何）
        const toolbarRow = seg ? seg.parentElement : null;
        out.chipRowH = toolbarRow ? Math.round(toolbarRow.getBoundingClientRect().height) : null;
        out.expectToolbarH = parseFloat(getComputedStyle(root).getPropertyValue('--toolbar-h'));
        // 保持在浏览态：主进程随后截图取证；复位交给后续 store 探针的 resetViewFilters
        return out;
      })()`) as Record<string, unknown>
      {
        const p = page as Record<string, unknown>
        if (p.fatal) throw new Error(`页面走查: ${p.fatal}`)
        const problems: string[] = []
        if ((p.cards as number) < 1) problems.push('画廊无卡片')
        if (p.cardChip !== true || p.cardChipSvg !== true) problems.push('卡片缺语义图标 chip')
        if (p.cardChipText !== '') problems.push(`图标 chip 内含文本（emoji 残留？）: ${p.cardChipText}`)
        if (p.cardEmoji || p.cardsEmoji || p.sectionEmoji) problems.push('页面仍有 emoji 文本')
        if (p.cardTitleWeight !== '600') problems.push(`卡片标题字重 ${p.cardTitleWeight} != 600`)
        const allowed = ['400', '500', '600']
        const badWeights = (p.cardWeights as string[]).filter((w) => !allowed.includes(w))
        if (badWeights.length) problems.push(`卡片内非标字重: ${badWeights.join(',')}`)
        if (!p.sectionChipSvg) problems.push('分区头缺语义图标')
        if (p.seg !== true) problems.push('浏览态缺分段控件')
        if (p.segCount !== 2) problems.push(`分段控件按钮数 ${p.segCount}`)
        if (p.segActive !== true) problems.push('分段控件无选中段')
        if (p.chipRowH === null || Math.abs((p.chipRowH as number) - (p.expectToolbarH as number)) > 1) {
          problems.push(`工具条高 ${p.chipRowH} != --toolbar-h ${p.expectToolbarH}`)
        }
        if (problems.length) throw new Error('画廊页面走查失败: ' + problems.join('; '))
        // 走查取证：SMOKE_SHOTS=<dir> 时截浏览态（不带系统窗口装饰，纯页面布局）
        if (process.env.SMOKE_SHOTS) {
          try {
            await new Promise((r) => setTimeout(r, 400))
            const shot = await mainWindow!.webContents.capturePage()
            fs.writeFileSync(path.join(process.env.SMOKE_SHOTS, 'gallery-browse.png'), shot.toPNG())
          } catch (e) {
            console.error('[smoke] 截图失败:', (e as Error).message)
          }
        }
        const mode = p.segActiveBg === p.expectPressedBg ? '抬起段(mac)' : p.segActiveColor === p.expectAccentText ? '强调下划线(win)' : '未知'
        console.log(`[smoke] 画廊走查通过：分区 ${p.sections} 卡片 ${p.cards} 图标 chip ✓ 字重 ${(p.cardWeights as string[]).join('/')} 分段 ${mode}`)
      }
      // 渲染层链路探针：经 window.__app 驱动 Vue 应用（store 状态 + 持久化 + 筛选）
      step = '渲染层链路探针'
      const probe = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const app = window.__app;
        if (!app) return { fatal: '__app 未注入（入口缺 ?smoke=1）' };
        app.resetViewFilters(); // 清掉本机残留的主题/搜索/收藏筛选，保证计数断言从干净态开始
        const out = {};
        // 1) 运行历史链路：清空（不依赖环境干净）→ recordHistory → userData 落盘 → 回读 → 清理
        await window.sidecar.store.set('history', []);
        app.resetRunHistory();
        const ex0 = app.examples()[0];
        const memAfter = await app.recordHistory({ id: ex0.id, name: ex0.name, args: [], startedAt: Date.now() - 42 }, 0);
        const saved = await window.sidecar.store.get('history');
        const histBad = !Array.isArray(saved) || saved.length !== 1 || saved[0].ok !== true || saved[0].duration_ms < 40;
        await window.sidecar.store.set('history', []);
        app.resetRunHistory();
        out.history = histBad ? 'BAD:' + JSON.stringify({ saved, memAfter }) : 'OK';
        // 2) 收藏链路：清空（残留收藏会让 toggle 方向与计数断言失真）→ 切换 → 落盘回读 → 只看收藏过滤组合 → 清理
        // 基准计数用相对比较：本机可能残留 viewPrefs 主题筛选（CI 干净环境无此问题），
        // 断言本意是「favOnly 过滤生效且关闭后复原」而非「环境处于默认态」
        await window.sidecar.store.set('favorites', []);
        const baseCount = app.filteredCount();
        const id = app.examples().find((e) => e.category !== 'tools').id; // 收藏样本须画廊可见（工具不进画廊池）
        const on = app.toggleFavorite(id);
        await sleep(300);
        const favs = await window.sidecar.store.get('favorites');
        app.setFavOnly(true);
        const favCount = app.filteredCount();
        app.setFavOnly(false);
        const allCount = app.filteredCount();
        await window.sidecar.store.set('favorites', []);
        app.toggleFavorite(id); // 复位内存态
        const favBad = !on || !Array.isArray(favs) || favs.length !== 1 || favs[0] !== id ||
          favCount !== 1 || allCount !== baseCount;
        out.favorites = favBad ? 'BAD:' + JSON.stringify({ on, favs, favCount, allCount }) : 'OK';
        // 3) 多维筛选：标签 facet 非空、选中后过滤生效、清除后复原（复原基准用进入时计数，
        //    不假设 viewPrefs 无残留主题筛选）
        const facets = app.tagFacetsFor('gallery');
        const facetsBase = app.filteredCount();
        if (!facets.length) out.facets = 'BAD:no-facets';
        else {
          const tag = facets[0].tag;
          app.setTags([tag]);
          const byTag = app.filteredCount();
          app.setTags([]);
          const restored = app.filteredCount() === facetsBase;
          out.facets = byTag > 0 && restored ? 'OK' : 'BAD:' + JSON.stringify({ byTag, restored });
        }
        // 4) 画廊池不含工具：干净筛选态下 filtered 计数 = 全集 − tools 数（工具只待在工具箱）
        const allEx = app.examples();
        const toolN = allEx.filter((e) => e.category === 'tools').length;
        const galleryN = app.filteredCount();
        out.gallery = toolN > 0 && galleryN === allEx.length - toolN ? 'OK' : 'BAD:' + JSON.stringify({ all: allEx.length, toolN, galleryN });
        // 5) AI 代码解释：设置读写 roundtrip + 无 key 优雅降级 + key 不回传明文
        await window.sidecar.ai.setSettings({ apiKey: "sk-test-fake-key", model: "deepseek-chat", baseUrl: "https://api.deepseek.com" });
        const s1 = await window.sidecar.ai.getSettings();
        if (!s1.hasKey) { out.ai = 'BAD:set_not_persisted'; return out; }
        if (s1.apiKey && s1.apiKey !== "********") { out.ai = 'BAD:key_leaked'; return out; }
        await window.sidecar.ai.setSettings({ apiKey: "" });
        const s2 = await window.sidecar.ai.getSettings();
        if (s2.hasKey) { out.ai = 'BAD:key_not_cleared'; return out; }
        const r = await window.sidecar.ai.explain("print(1)", "t.py");
        await window.sidecar.ai.setSettings({ acknowledged: false });
        out.ai = r && r.error === "no_api_key" ? 'OK' : 'BAD:' + JSON.stringify(r);
        return out;
      })()`) as Record<string, string>
      for (const key of ['history', 'favorites', 'facets', 'gallery', 'ai']) {
        const v = probe[key]
        if (v !== 'OK') throw new Error(`${key} 链路异常: ${v}`)
        console.log(`[smoke] ${key} 链路正常`)
      }
      // 详情 / 运行器走查（A4）：打开的详情页里量头部语言、标签页、终端面与字重白名单
      step = '详情页走查'
      const detail = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const root = document.documentElement;
        const cs = getComputedStyle(root);
        const px = (v) => parseFloat(v);
        const emojiRe = /[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}]/u;
        const out = {};
        const app = window.__app;
        if (!app) return { fatal: '__app 未注入' };
        const picks = app.examples().filter((e) => e.category !== 'tools');
        if (!picks.length) return { fatal: '没有可打开的示例' };
        await app.openDetail(picks[0].id);
        await sleep(2500); // Monaco 懒加载 + 首次布局
        const host = document.querySelector('[role="tablist"][aria-label="输出面板"]');
        if (!host) return { fatal: '详情页未打开（无标签页）' };
        // 1) 标签页：三个 .tab + 选中语义（aria-selected 为真值来源）
        const tabs = Array.from(host.querySelectorAll('.tab'));
        out.tabs = tabs.length;
        out.tabSelected = tabs.filter((t) => t.getAttribute('aria-selected') === 'true').length;
        out.tabRowH = Math.round(host.getBoundingClientRect().height);
        out.expectPaneHeadH = px(cs.getPropertyValue('--pane-head-h'));
        // 2) 终端/代码面：底色与文字必须等于跟随主题的令牌
        const probeConsole = document.createElement('div');
        probeConsole.style.cssText = 'position:absolute;visibility:hidden;background:var(--bg-console);color:var(--text-console)';
        document.body.appendChild(probeConsole);
        out.expectConsoleBg = getComputedStyle(probeConsole).backgroundColor;
        out.expectConsoleFg = getComputedStyle(probeConsole).color;
        probeConsole.remove();
        const consoleEl = document.querySelector('.console');
        out.hasConsole = !!consoleEl;
        if (consoleEl) {
          const ccs = getComputedStyle(consoleEl);
          out.consoleBg = ccs.backgroundColor;
          out.consoleFg = ccs.color;
          out.consoleMono = ccs.fontFamily.toLowerCase().includes('mono') || ccs.fontFamily.toLowerCase().includes('menlo') || ccs.fontFamily.toLowerCase().includes('cascadia');
        }
        // 3) 头部：图标 chip + 无 emoji（只看 chrome）
        const header = document.querySelector('main section .chip-ic');
        out.headChip = !!header;
        out.headerEmoji = emojiRe.test(document.querySelector('main section')?.textContent?.slice(0, 400) || '');
        // 4) 字重白名单（详情页 chrome 抽样）
        const weights = new Set();
        for (const el of document.querySelectorAll('main section *')) {
          const w = getComputedStyle(el).fontWeight;
          if (w) weights.add(w);
        }
        out.weights = Array.from(weights).sort();
        return out;
      })()`) as Record<string, unknown>
      {
        const d = detail as Record<string, unknown>
        if (d.fatal) throw new Error(`详情页走查: ${d.fatal}`)
        const problems: string[] = []
        if (d.tabs !== 3) problems.push(`标签页数 ${d.tabs} != 3`)
        if (d.tabSelected !== 1) problems.push(`选中标签数 ${d.tabSelected} != 1`)
        if (Math.abs((d.tabRowH as number) - (d.expectPaneHeadH as number)) > 1) {
          problems.push(`标签行高 ${d.tabRowH} != --pane-head-h ${d.expectPaneHeadH}`)
        }
        if (!d.hasConsole) problems.push('详情页缺终端输出面（.console）')
        if (d.consoleBg !== d.expectConsoleBg) problems.push(`终端底色 ${d.consoleBg} != --bg-console ${d.expectConsoleBg}`)
        if (d.consoleFg !== d.expectConsoleFg) problems.push(`终端文字 ${d.consoleFg} != --text-console ${d.expectConsoleFg}`)
        if (!d.consoleMono) problems.push('终端面未使用等宽栈')
        if (!d.headChip) problems.push('详情头部缺图标 chip')
        if (d.headerEmoji) problems.push('详情头部仍有 emoji')
        const badW = (d.weights as string[]).filter((w) => !['400', '500', '600'].includes(w))
        if (badW.length) problems.push(`详情页非标字重: ${badW.join(',')}`)
        if (problems.length) throw new Error('详情页走查失败: ' + problems.join('; '))
        // 走查取证：详情页（左代码 / 右输出面板）截图
        if (process.env.SMOKE_SHOTS) {
          try {
            await new Promise((r) => setTimeout(r, 400))
            const shot = await mainWindow!.webContents.capturePage()
            fs.writeFileSync(path.join(process.env.SMOKE_SHOTS, 'detail.png'), shot.toPNG())
          } catch (e) {
            console.error('[smoke] 截图失败:', (e as Error).message)
          }
        }
        console.log(`[smoke] 详情走查通过：标签 ${d.tabs} 选中 ${d.tabSelected} 标签行高 ${d.tabRowH} 终端底 ${d.consoleBg} 字重 ${(d.weights as string[]).join('/')}`)
      }
      // 全局层走查（A5）：命令面板选中语义（板 3）+ 高危确认弹层按钮序与危险语义（板 4）
      step = '全局层走查'
      const overlay = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const root = document.documentElement;
        const isWin = root.getAttribute('data-platform') === 'win';
        const reg = (el) => el ? el.getBoundingClientRect() : null;
        const out = { isWin, modKey: isWin ? 'Ctrl' : '\u2318' };
        const token = (name) => {
          const probe = document.createElement('div');
          probe.style.cssText = 'position:absolute;visibility:hidden;' + name;
          document.body.appendChild(probe);
          const v = getComputedStyle(probe);
          const res = [v.backgroundColor, v.color].join('|');
          probe.remove();
          return res;
        };
        out.expectAccentBg = token('background:var(--accent)').split('|')[0];
        out.expectSubtleBg = token('background:var(--bg-subtle)').split('|')[0];
        out.expectDangerText = token('color:var(--status-red)').split('|')[1];

        // 1) 命令面板：真实快捷键打开
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true, ctrlKey: true, bubbles: true }));
        await sleep(500);
        // 结构锚点：搜索框 → 搜索行 → 面板（版本无关，避免用 A5 才有的类名做定位）
        const input = document.querySelector('input[aria-label="全局搜索示例"]');
        const palette = input ? input.parentElement && input.parentElement.parentElement : null;
        out.paletteOpen = !!palette;
        if (!palette) return { fatal: '命令面板未打开' };
        const rows = Array.from(palette.querySelectorAll('[data-active]'));
        out.rows = rows.length;
        const active = rows.find((r) => r.getAttribute('data-active') === 'true');
        out.hasActive = !!active;
        out.activeBg = active ? getComputedStyle(active).backgroundColor : 'NO-ACTIVE';
        out.footText = (palette.lastElementChild?.textContent || '').trim();

        // 帮助面板：⌘/ 打开 → 键位表 + 环境信息取自真实来源 → Esc 关闭
        window.dispatchEvent(new KeyboardEvent('keydown', { key: '/', metaKey: true, ctrlKey: true, bubbles: true }));
        await sleep(400);
        const help = document.querySelector('[aria-label="帮助与快捷键"]');
        out.helpOpen = !!help;
        if (help) {
          out.helpKbds = help.querySelectorAll('kbd').length;
          out.helpHasSafety = (help.textContent || '').includes('不是安全沙箱');
          // 断言用整段文本：环境信息段在面板末尾，截断取样会漏
          out.helpHasPython = new RegExp('Python [0-9]+[.][0-9]+').test(help.textContent || '');
          out.helpHasVersion = !!(window.__app.envStatus() && window.__app.envStatus().venv_path);
          window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
          await sleep(250);
          out.helpClosed = !document.querySelector('[aria-label="帮助与快捷键"]');
          // 关帮助不得连带关掉底下的命令面板？（此处面板已先关，仅校验互不干扰）
        }

        // 2) 高危确认：经 store 打开一个高危示例并触发运行（四个入口都汇聚到同一守卫），
        //    走的是真实链路而非注入状态；确认弹层出现后立即取消，不真跑
        const app = window.__app;
        const risky = app.examples().find((e) => e.risk_high);
        out.riskyId = risky ? risky.id : null;
        if (!risky) return { fatal: '数据里没有 risk_high 示例，无法走查确认弹层' };
        await app.openDetail(risky.id);
        await sleep(700);
        app.runFromDetail();
        await sleep(900);
        const dialog = document.querySelector('[role="dialog"]');
        out.dialogOpen = !!dialog;
        if (dialog) {
          out.alertline = !!dialog.querySelector('.alertline');
          const al = dialog.querySelector('.alertline');
          out.alertBg = al ? getComputedStyle(al).backgroundColor : 'MISSING';
          out.alertIconColor = al && al.querySelector('svg') ? getComputedStyle(al.querySelector('svg')).color : 'MISSING';
          const act = dialog.querySelector('.d-actions');
          out.hasActions = !!act;
          if (act) {
            const btns = Array.from(act.querySelectorAll('button'));
            out.btns = btns.map((b) => b.textContent.trim());
            const danger = btns.find((b) => b.textContent.includes('仍要运行'));
            const cancel = btns.find((b) => b.textContent.includes('取消'));
            out.dangerColor = danger ? getComputedStyle(danger).color : 'MISSING';
            if (danger && cancel) {
              const d = reg(danger), c = reg(cancel);
              out.order = d.left < c.left ? 'danger-first' : 'cancel-first';
            }
          }
        }
        return out;
      })()`) as Record<string, unknown>
      {
        const o = overlay as Record<string, unknown>
        if (o.fatal) throw new Error(`全局层走查: ${o.fatal}`)
        const problems: string[] = []
        // 命令面板（板 3）
        if (!o.paletteOpen) problems.push('命令面板未打开')
        if ((o.rows as number) < 1) problems.push('命令面板无行')
        if (!o.hasActive) problems.push('命令面板无选中行')
        const expectBg = o.isWin ? o.expectSubtleBg : o.expectAccentBg
        if (o.activeBg !== expectBg) problems.push(`面板选中底 ${o.activeBg} != ${expectBg}`)
        if (!String(o.footText || '').includes(String(o.modKey))) {
          problems.push(`面板底部提示缺平台修饰键 ${o.modKey}：${o.footText}`)
        }
        // 帮助面板（A5.5 板 1）
        if (!o.helpOpen) problems.push('⌘/ 未打开帮助面板')
        if ((o.helpKbds as number) < 7) problems.push(`帮助键位表不足 7 条（${o.helpKbds}）`)
        if (!o.helpHasSafety) problems.push('帮助缺安全边界段')
        if (!o.helpHasPython) problems.push('帮助的环境信息未显示 Python 版本（未接真实来源？）')
        if (o.helpHasVersion !== true) problems.push('渲染层未持有 sidecar 的 env_status')
        if (o.helpClosed !== true) problems.push('Esc 未关闭帮助面板')
        // 高危确认（板 4）
        if (!o.dialogOpen) problems.push('高危卡片未触发确认弹层')
        if (!o.alertline) problems.push('确认弹层缺 .alertline')
        if (o.isWin) {
          if (o.alertBg === 'rgba(0, 0, 0, 0)') problems.push('win 弹层未使用 InfoBar 语义底')
          if (o.order !== 'danger-first') problems.push(`win 按钮序应为危险在前（当前 ${o.order}）`)
        } else {
          if (o.alertBg !== 'rgba(0, 0, 0, 0)') problems.push(`mac 弹层应为平面（当前底 ${o.alertBg}）`)
          if (o.order !== 'cancel-first') problems.push(`mac 按钮序应为主操作最后（当前 ${o.order}）`)
        }
        if (o.dangerColor !== o.expectDangerText) {
          problems.push(`危险按钮不是红字（${o.dangerColor} != ${o.expectDangerText}）`)
        }
        if (problems.length) throw new Error('全局层走查失败: ' + problems.join('; '))
        console.log(
          `[smoke] 全局层走查通过：面板 ${o.rows} 行 选中底 ${o.activeBg} 底部「${o.footText}」；弹层 ${o.btns} 序 ${o.order} 危险色 ${o.dangerColor}`
        )
      }
      // 走查取证：面板 →（关面板后）高危确认弹层，各截一张
      if (process.env.SMOKE_SHOTS) {
        const shot = async (name: string): Promise<void> => {
          try {
            await new Promise((r) => setTimeout(r, 400))
            fs.writeFileSync(
              path.join(process.env.SMOKE_SHOTS!, name),
              (await mainWindow!.webContents.capturePage()).toPNG()
            )
          } catch (e) {
            console.error(`[smoke] 截图失败(${name}):`, (e as Error).message)
          }
        }
        await shot('palette.png')
        await mainWindow!.webContents.executeJavaScript('window.__app.openHelp()')
        await new Promise((r) => setTimeout(r, 500))
        await shot('help.png')
        await mainWindow!.webContents.executeJavaScript('window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }))')
        await new Promise((r) => setTimeout(r, 400))
        // 详情页仍开着：重新触发一次确认弹层再截图（弹层在面板之下，需先关面板）
        await mainWindow!.webContents.executeJavaScript('window.__app.runFromDetail()')
        await new Promise((r) => setTimeout(r, 700))
        await shot('highrisk-dialog.png')
      }
      // 收尾：取消高危确认，避免残留弹层影响后续探针
      await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const cancel = Array.from(document.querySelectorAll('[role="dialog"] .d-actions button')).find((b) => b.textContent.includes('取消'));
        if (cancel) cancel.click();
        await sleep(200);
      })()`)
      // 首启引导页走查（A5.5 板 2/3）：展示 → 状态来自 sidecar → 开始浏览写标记并关闭
      step = '首启引导走查'
      const ob = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        try {
        const app = window.__app;
        if (!app || !app.showOnboarding) return { fatal: '__app 未注入或缺少 showOnboarding' };
        const out = {};
        await window.sidecar.store.set('onboarding', null);
        app.showOnboarding();
        await sleep(500);
        const card = document.querySelector('[data-testid="onboarding"]');
        out.open = !!card;
        if (!card) return { fatal: '首启引导页未展示' };
        out.text = (card.textContent || '').slice(0, 200);
        out.hasStart = /开始浏览/.test(card.textContent || '');
        out.steps = card.querySelectorAll('.stat-dot, .ring, .spinner').length;
        // 环境事实必须来自 sidecar：比对刚拉到的 env_status
        const st = await window.sidecar.env.status();
        out.envPhase = st.phase;
        out.envPython = st.python_version;
        out.cardHasPython = (card.textContent || '').includes('Python');
        // 「开始浏览」：写标记 + 关闭
        const start = Array.from(card.querySelectorAll('button')).find((b) => b.textContent.includes('开始浏览'));
        if (!start) return { fatal: '首启页缺「开始浏览」' };
        start.click();
        await sleep(500);
        out.closed = !document.querySelector('[data-testid="onboarding"]');
        const saved = await window.sidecar.store.get('onboarding');
        out.flagSeen = !!(saved && saved.seen);
        out.storeOpen = app.onboardingOpen();
        return out;
        } catch (e) { return { fatal: 'probe exception: ' + ((e && e.message) || String(e)) }; }
      })()`) as Record<string, unknown>
      {
        const o = ob as Record<string, unknown>
        if (o.fatal) throw new Error(`首启引导走查: ${o.fatal}`)
        const problems: string[] = []
        if (!o.open) problems.push('首启页未展示')
        if (!o.hasStart) problems.push('缺「开始浏览」入口')
        if ((o.steps as number) < 4) problems.push(`步骤标记不足（${o.steps}）`)
        if (!o.envPhase) problems.push('未取到 sidecar 环境状态')
        if (!o.envPython) problems.push('sidecar 未上报 Python 版本')
        if (!o.cardHasPython) problems.push('首启页未呈现环境信息（数据未接线？）')
        if (o.closed !== true) problems.push('「开始浏览」未关闭首启页')
        if (o.flagSeen !== true) problems.push('未写入首启标记（会每次启动都弹）')
        if (o.storeOpen !== false) problems.push('store 的 onboardingOpen 未复位')
        if (problems.length) throw new Error('首启引导走查失败: ' + problems.join('; '))
        console.log(`[smoke] 首启走查通过：phase=${o.envPhase} python=${o.envPython} 步骤标记 ${o.steps} 个，标记已写入`)
        if (process.env.SMOKE_SHOTS) {
          try {
            await mainWindow!.webContents.executeJavaScript('window.__app.showOnboarding()')
            await new Promise((r) => setTimeout(r, 500))
            const shot = await mainWindow!.webContents.capturePage()
            fs.writeFileSync(path.join(process.env.SMOKE_SHOTS, 'onboarding.png'), shot.toPNG())
            await mainWindow!.webContents.executeJavaScript('window.__app.dismissOnboarding()')
            await new Promise((r) => setTimeout(r, 200))
          } catch (e) {
            console.error('[smoke] 截图失败(onboarding.png):', (e as Error).message)
          }
        }
      }
      // 5) 用户集合导入/删除链路：tmp 目录 → import → 数量与标记 → delete → 复原
      step = '用户集合导入/删除'
      const tmpImportDir = fs.mkdtempSync(path.join(os.tmpdir(), 'smoke-import-'))
      const importedIds = ['smoke_a.py', 'smoke_b.py']
      try {
        fs.writeFileSync(path.join(tmpImportDir, 'smoke_a.py'), 'print("a")\n', 'utf-8')
        fs.writeFileSync(path.join(tmpImportDir, 'smoke_b.py'), 'print("b")\n', 'utf-8')
        const before = (await callSidecar('list_examples')) as { total: number }
        const imp = (await callSidecar('import_examples', {
          source_path: tmpImportDir,
          name: 'smoke_import'
        })) as { imported: number; collection: string | null }
        const after = (await callSidecar('list_examples')) as {
          total: number
          examples: Array<{ id: string; user_collection?: boolean }>
        }
        const newUser = (after.examples || []).find((e) => e.id === 'smoke_a.py')
        const okImport =
          imp.imported === 2 &&
          imp.collection === 'smoke_import' &&
          after.total === before.total + 2 &&
          !!newUser &&
          newUser.user_collection === true
        const del1 = (await callSidecar('delete_example', { id: 'smoke_a.py' })) as { deleted?: string }
        const del2 = (await callSidecar('delete_example', { id: 'smoke_b.py' })) as { deleted?: string }
        const final = (await callSidecar('list_examples')) as { total: number }
        const okDelete = !!del1.deleted && !!del2.deleted && final.total === before.total
        if (!okImport || !okDelete) {
          throw new Error(
            `导入链路异常: ${JSON.stringify({ imported: imp.imported, collection: imp.collection, before: before.total, after: after.total, del1: del1.deleted, final: final.total })}`
          )
        }
        console.log('[smoke] 导入/删除链路正常')
      } finally {
        // 中途失败时也要复原：删掉本步导入的示例（集合被删空后文件会自动移除，
        // 否则 user_examples/smoke_import.json 会留在开发机上，且被 .gitignore 掩盖）。
        // 注：deadline 触发的硬超时走 app.exit，不会执行到这里。
        for (const id of importedIds) {
          try {
            await callSidecar('delete_example', { id })
          } catch {
            // 该示例可能已被本步正常删除，忽略
          }
        }
        fs.rmSync(tmpImportDir, { recursive: true, force: true })
      }
      // 留 8s 让渲染进程完成 Monaco 初始化与列表渲染，捕获潜在 console error
      step = '渲染层错误观察窗'
      await new Promise((r) => setTimeout(r, 8000))
      if (failures.length) {
        console.error('[smoke] 渲染进程报错:\n' + failures.join('\n'))
        app.exit(1)
        return
      }
      clearTimeout(deadline)
      console.log('[smoke] 全部通过')
      app.exit(0)
    } catch (err) {
      clearTimeout(deadline)
      console.error('[smoke] 失败:', (err as Error).message)
      app.exit(1)
    }
  })()
}

// ---------------------------------------------------------------------------
// E2E 自测（E2E_TEST=1）：驱动 Vue 详情页完整闭环并断言（无需人工交互/显示）
// 覆盖：详情打开与参数解析 → 填参运行 → 输出回显 → 历史记录 → 参数回填
// ---------------------------------------------------------------------------
function runE2ETest(): void {
  const deadline = setTimeout(() => {
    console.error('[e2e] 60s 内未完成，判定失败')
    app.exit(1)
  }, 60000)

  void (async () => {
    try {
      // 等待示例加载完成
      for (let i = 0; i < 60; i++) {
        const n = await mainWindow!.webContents.executeJavaScript('window.__app ? window.__app.examples().length : 0') as number
        if (n > 100) break
        await new Promise((r) => setTimeout(r, 300))
      }
      const report = await mainWindow!.webContents.executeJavaScript(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, 300));
        const app = window.__app;
        if (!app) return { fatal: '__app 未注入（入口缺 ?smoke=1）' };
        const out = {};
        // 运行链路需要「有 argparse 参数 + 打印回显 + 无第三方依赖」的示例：
        // crawler_eng-cli-argparse.py（--pages/--keyword/--output）正合此用途
        const ex = app.findByName('crawler_eng-cli-argparse.py');
        if (!ex) return { fatal: 'crawler_eng-cli-argparse.py 不在示例列表中' };

        // 1) 打开详情页 → 参数解析（cli_greeting 有 --name/-r 两个可选参数）
        const args = await app.openDetail(ex.id);
        out.argsParsed = Array.isArray(args) ? args.length : -1;

        // 2) 填参 → 收集 → 运行（idx 1 = --keyword，字符串型便于回显断言）
        app.setArgValue(1, 'E2E测试');
        out.collectedArgs = JSON.stringify(app.collectArgs());
        app.runFromDetail();

        // 3) 等待运行结束（最多 25s）
        for (let i = 0; i < 80; i++) {
          if (!app.isRunning()) break;
          await sleep(300);
        }
        out.runFinished = !app.isRunning();
        out.outputText = app.outputText() || '';
        out.outputHasGreeting = out.outputText.includes('E2E测试');
        out.runStatusText = app.runStatusText();

        // 4) 内嵌历史与重跑参数回填
        out.historyCount = app.detailHistory().length;
        const lastArgs = (app.runHistory()[0] && app.runHistory()[0].args) || [];
        app.backfillArgs(lastArgs);
        out.backfilledArgs = JSON.stringify(app.collectArgs());

        // 5) 资源标签：空态
        out.assetsCount = app.assets().length;

        // 清理测试历史
        await window.sidecar.store.set('history', []);
        app.resetRunHistory();
        return out;
      })()`) as Record<string, unknown>

      console.log('[e2e] 探针结果:', JSON.stringify(report, null, 1))
      const r = report as Record<string, unknown>
      const fail =
        r.fatal ||
        (r.argsParsed as number) < 1 ||
        r.runFinished !== true ||
        r.outputHasGreeting !== true ||
        r.runStatusText !== '运行成功' ||
        (r.historyCount as number) < 1 ||
        !(r.backfilledArgs as string).includes('E2E测试') ||
        (r.assetsCount as number) !== 0
      if (fail) {
        console.error('[e2e] 断言失败')
        clearTimeout(deadline)
        app.exit(1)
        return
      }
      clearTimeout(deadline)
      console.log('[e2e] 全部通过')
      app.exit(0)
    } catch (err) {
      clearTimeout(deadline)
      console.error('[e2e] 失败:', (err as Error).message)
      app.exit(1)
    }
  })()
}

// ---------------------------------------------------------------------------
// 全局异常兜底：未捕获异常不直接崩溃，记录日志并尝试通知渲染层
// ---------------------------------------------------------------------------
process.on('uncaughtException', (err: Error) => {
  console.error('[main] uncaughtException:', err)
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
    runSmokeTest()
  }

  if (process.env.E2E_TEST) {
    runE2ETest()
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
    // macOS 关窗后从 Dock 重开：窗口重建的同时恢复 sidecar
    // （此前只重建窗口，sidecar 若已退出则应用不可用）
    if (!sidecarProcess && !(app as any).isQuitting) {
      spawnSidecar()
    }
  })
})

// isQuitting 此前只被读取从未赋值：退出阶段 sidecar 被 kill 后 close 事件
// 仍走"崩溃"分支排定 2 秒后重启，可产生僵尸 sidecar；必须在退出起点置位
app.on('before-quit', () => {
  ;(app as any).isQuitting = true
})

app.on('window-all-closed', () => {
  if (sidecarProcess) {
    sidecarProcess.kill()
  }
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
