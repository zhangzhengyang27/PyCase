// prefs.ts：持久化的用户数据（收藏 / 运行历史 / 运行偏好 / 安全偏好）。
//
// 与纯 UI 状态的区别：这些值落在主进程 userData（store:* IPC），跨启动保留；
// 上层域（catalog/detail/runner）只读写这里，不各自散落持久化逻辑。
import { ref } from 'vue'
import type { RunHistoryEntry } from '../types'
import { api } from '../sidecar-client'

/** 运行历史上限（与详情页面板展示条数无关，防止无限增长） */
const HISTORY_CAP = 500

export const favorites = ref(new Set<string>())
export const runHistory = ref<RunHistoryEntry[]>([])
/** 运行超时（秒）：超时强制终止；设置弹窗「运行」分区可调，存 runPrefs */
export const runTimeout = ref(120) // 原生 turtle 窗口等交互式运行需要较长存活时间（设置可调 5~600）
/** 高危确认开关（设置弹窗「安全」分区）：与确认弹窗的「不再提示」共用同一持久化键 */
export const skipHighRiskConfirm = ref(false)

/** Vue 响应式 Proxy 不能跨 ipcRenderer.invoke 结构化克隆，IPC 传参一律深拷贝为普通对象 */
export function toPlain<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export function toggleFavorite(id: string | undefined): boolean {
  if (!id) return false
  const next = new Set(favorites.value)
  const faved = !next.has(id)
  if (faved) next.add(id)
  else next.delete(id)
  favorites.value = next // 整体替换触发依赖更新（Set 内部变更同样被追踪，替换语义更直白）
  api.storeSet('favorites', Array.from(next)).catch(() => {})
  // 不弹 toast：星标本身已是即时状态反馈，连点收藏时右下角会刷屏
  return faved
}

export function isFavorite(id: string | undefined): boolean {
  return !!id && favorites.value.has(id)
}

/** 高危确认开关（设置弹窗「安全」分区）：与确认弹窗的「不再提示」共用同一持久化键 */
export function setSkipHighRiskConfirm(skip: boolean): void {
  skipHighRiskConfirm.value = skip
  api.storeSet('safetyPrefs', { skipHighRiskConfirm: skip }).catch(() => {})
}

/** 调整并持久化运行超时（秒） */
export function setRunTimeout(seconds: number): void {
  runTimeout.value = seconds
  api.storeSet('runPrefs', { timeout: seconds }).catch(() => {})
}

export function recordHistory(
  meta: { id: string; name: string; args: string[]; startedAt: number },
  exitCode: number
): void {
  const entry: RunHistoryEntry = {
    ts: new Date().toISOString(),
    id: meta.id,
    name: meta.name,
    args: meta.args,
    duration_ms: Math.max(0, Date.now() - meta.startedAt),
    exit_code: exitCode,
    ok: exitCode === 0
  }
  runHistory.value = [entry, ...runHistory.value].slice(0, HISTORY_CAP)
  void persistRunHistory()
}

function persistRunHistory(): Promise<unknown> {
  return api.storeSet('history', toPlain(runHistory.value)).catch((err) => {
    console.error('[store] 运行历史持久化失败:', err)
    return undefined
  })
}

// ---------------------------------------------------------------------------
// 启动装载与持久化应用（loadAll 用；各域不各自解析存储格式）
// ---------------------------------------------------------------------------
export function applyHistory(raw: unknown): void {
  runHistory.value = Array.isArray(raw) ? (raw as RunHistoryEntry[]) : []
}

export function applyFavorites(raw: unknown): void {
  favorites.value = new Set(Array.isArray(raw) ? raw.map(String) : [])
}

export function applySafety(prefs: unknown): void {
  skipHighRiskConfirm.value = !!(prefs as Record<string, unknown> | null)?.skipHighRiskConfirm
}

export function applyRunPrefs(prefs: unknown): void {
  const t = (prefs as Record<string, unknown> | null)?.timeout
  if (typeof t === 'number' && t >= 5 && t <= 600) runTimeout.value = t
}
