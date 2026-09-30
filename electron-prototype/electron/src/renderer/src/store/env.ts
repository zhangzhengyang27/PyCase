// env.ts：环境准备与全局层开关域（首启引导页 / 帮助面板 / 应用信息）。
//
// 环境事实由 sidecar 上报（env_status + env_progress 通知），前端不猜：
// phase 推进顺序 preparing → indexing → warming → ready，失败进 failed 并带原因。
import { ref } from 'vue'
import { pushToast } from '../../toast'
import { api } from '../sidecar-client'

// ---------------------------------------------------------------------------
// 环境事实由 sidecar 上报（env_status + env_progress 通知），前端不猜：
// phase 推进顺序 preparing → indexing → warming → ready，失败进 failed 并带原因。
// ===========================================================================
export interface EnvStatus {
  phase: 'starting' | 'preparing' | 'indexing' | 'warming' | 'ready' | 'failed'
  /** 失败发生在哪一步（sidecar 上报；仅 phase=failed 时有意义） */
  failed_at?: 'starting' | 'preparing' | 'indexing' | 'warming'
  started_at?: number
  elapsed_ms?: number
  error?: string
  log_path?: string
  mode: 'shared' | 'system'
  venv_path?: string
  venv_ready?: boolean
  python_version?: string
  examples?: number
}

export const envStatus = ref<EnvStatus | null>(null)
export const onboardingOpen = ref(false)
export const helpOpen = ref(false)
export const appInfo = ref<{ name?: string; version?: string; electron?: string }>({})

function applyEnvStatus(next: unknown): void {
  if (next && typeof next === 'object') envStatus.value = next as EnvStatus
}

/** 订阅环境阶段推进 + 拉一次当前状态（首启页打开时补全量）。 */
export function initEnvEvents(): void {
  api.on('envProgress', (data) => applyEnvStatus(data))
  void refreshEnvStatus()
}

export async function refreshEnvStatus(): Promise<void> {
  try {
    applyEnvStatus(await api.envStatus())
  } catch (err) {
    console.error('[env] 读取环境状态失败:', err)
  }
}

export async function loadAppInfo(): Promise<void> {
  try {
    appInfo.value = (await api.appInfo()) as { name?: string; version?: string; electron?: string }
  } catch (err) {
    console.error('[env] 读取应用信息失败:', err)
  }
}

/** 首启引导：只在本地标记缺失时展示（首帧后，不等 sidecar ready）。 */
export async function loadOnboarding(): Promise<void> {
  try {
    const seen = (await api.storeGet('onboarding')) as { seen?: boolean } | null
    onboardingOpen.value = !seen?.seen
  } catch {
    onboardingOpen.value = true
  }
}

export async function dismissOnboarding(): Promise<void> {
  onboardingOpen.value = false
  try {
    await api.storeSet('onboarding', { seen: true, at: Date.now() })
  } catch (err) {
    console.error('[env] 写入引导标记失败:', err)
  }
}

/** 「用系统 Python 继续」：切换运行解释器模式（sidecar 侧生效，不改共享环境）。 */
export async function useSystemPython(): Promise<void> {
  try {
    applyEnvStatus(await api.setRunEnv('system'))
  } catch (err) {
    console.error('[env] 切换解释器模式失败:', err)
  }
}

/** 「重试」：重启 sidecar（其启动流程会重新预热共享环境并重发阶段事件）。 */
export async function retryEnvPrepare(): Promise<void> {
  try {
    await api.restart()
    await refreshEnvStatus()
  } catch (err) {
    console.error('[env] 重试环境准备失败:', err)
  }
}

export async function openLog(): Promise<void> {
  try {
    const r = (await api.openLog()) as { ok?: boolean; error?: string }
    if (r && r.ok === false && r.error) pushToast('error', r.error)
  } catch (err) {
    console.error('[env] 打开日志失败:', err)
  }
}

export function openHelp(): void {
  helpOpen.value = true
}
export function closeHelp(): void {
  helpOpen.value = false
}

// ---------------------------------------------------------------------------
// 测试钩子（环境与全局层）：由 store/index.ts 的 getTestApi 组合成 window.__app
// ---------------------------------------------------------------------------
export function envTestHooks(): Record<string, unknown> {
  return {
    envStatus: () => envStatus.value,
    openHelp: () => openHelp(),
    helpOpen: () => helpOpen.value,
    onboardingOpen: () => onboardingOpen.value,
    dismissOnboarding: () => dismissOnboarding(),
    showOnboarding: () => {
      onboardingOpen.value = true
    }
  }
}
