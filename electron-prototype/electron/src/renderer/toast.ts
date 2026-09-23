// toast.ts：全局轻提示状态（ElMessage 的自建替代，无组件库依赖）
// 成功/信息 3s 自动退场，错误 8s；同屏上限 4 条（后到者顶掉最旧）；
// 悬停暂停倒计时，移出恢复；AppToast.vue 负责渲染。
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'info'
export interface ToastItem {
  id: number
  type: ToastType
  text: string
}

export const toasts = ref<ToastItem[]>([])
let seq = 0
const timers = new Map<number, number>()

const TIMEOUT_MS: Record<ToastType, number> = { success: 3000, info: 3000, error: 8000 }
const MAX_VISIBLE = 4

function scheduleDismiss(id: number, type: ToastType): void {
  timers.set(id, window.setTimeout(() => dismissToast(id), TIMEOUT_MS[type]))
}

export function pushToast(type: ToastType, text: string): void {
  const id = ++seq
  toasts.value.push({ id, type, text })
  // 超出上限：立即退场最旧的（含清理其定时器）
  while (toasts.value.length > MAX_VISIBLE) {
    const oldest = toasts.value[0]
    dismissToast(oldest.id)
  }
  scheduleDismiss(id, type)
}

export function holdToast(id: number): void {
  const timer = timers.get(id)
  if (timer !== undefined) {
    clearTimeout(timer)
    timers.delete(id)
  }
}

export function resumeToast(id: number): void {
  const toast = toasts.value.find((t) => t.id === id)
  if (toast && !timers.has(id)) scheduleDismiss(id, toast.type)
}

export function dismissToast(id: number): void {
  const timer = timers.get(id)
  if (timer !== undefined) {
    clearTimeout(timer)
    timers.delete(id)
  }
  toasts.value = toasts.value.filter((t) => t.id !== id)
}
