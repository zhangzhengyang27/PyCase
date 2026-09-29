// storage.ts：存储治理域（设置中心「存储」分区）。
//
// 数据全部来自 sidecar 的 storage_report / clean_workspace / reclaim_legacy_cache：
// 工作区占用（含用户资产条目明细）、v1 旧缓存根占用、编辑历史占用。
// 清理动作分两档（契约 §4.4）：clean 保留含用户资产的条目，all 需用户显式选择。
import { ref } from 'vue'
import { pushToast } from '../../toast'
import type { StorageReport } from '../../../../../shared/protocol'
import { api } from '../sidecar-client'

export const storageReport = ref<StorageReport | null>(null)
export const storageLoading = ref(false)
/** 正在执行的清理动作（'clean' | 'all' | 'legacy'），用于按钮 loading 态 */
export const storageBusy = ref<'' | 'clean' | 'all' | 'legacy'>('')

export async function loadStorageReport(): Promise<void> {
  storageLoading.value = true
  try {
    storageReport.value = await api.storageReport()
  } catch (err) {
    console.error('[storage] 读取存储占用失败:', err)
  } finally {
    storageLoading.value = false
  }
}

/** 两档清理：clean = 保留含用户资产的条目；all = 全部清（用户显式选择） */
export async function cleanWorkspace(mode: 'clean' | 'all'): Promise<void> {
  if (storageBusy.value) return
  storageBusy.value = mode
  try {
    const result = await api.cleanWorkspace(mode)
    const mb = (result.freed_bytes / 1024 / 1024).toFixed(1)
    pushToast('success', `已清理 ${result.removed} 个工作区，释放约 ${mb}MB`)
    if (result.kept > 0) pushToast('info', `${result.kept} 个含上传资源/运行产物的工作区已保留`)
    await loadStorageReport()
  } catch (err) {
    pushToast('error', `清理失败: ${(err as Error).message}`)
  } finally {
    storageBusy.value = ''
  }
}

/** 回收 v1 旧缓存根（旧版遗留的按示例目录） */
export async function reclaimLegacyCache(): Promise<void> {
  if (storageBusy.value) return
  storageBusy.value = 'legacy'
  try {
    const result = await api.reclaimLegacyCache()
    const mb = (result.freed_bytes / 1024 / 1024).toFixed(1)
    pushToast('success', `已回收旧缓存 ${result.removed} 项，释放约 ${mb}MB`)
    await loadStorageReport()
  } catch (err) {
    pushToast('error', `回收失败: ${(err as Error).message}`)
  } finally {
    storageBusy.value = ''
  }
}

// ---------------------------------------------------------------------------
// 测试钩子（存储治理）：由 store/index.ts 的 getTestApi 组合成 window.__app
// ---------------------------------------------------------------------------
export function storageTestHooks(): Record<string, unknown> {
  return {
    storageReport: () => storageReport.value,
    storageBusy: () => storageBusy.value,
    loadStorageReport: () => loadStorageReport(),
    cleanWorkspace: (mode: 'clean' | 'all') => cleanWorkspace(mode),
    reclaimLegacyCache: () => reclaimLegacyCache()
  }
}
