// import.ts：导入向导域（用户示例集合：选择目录 → 预览 → 导入 → 删除）。
import { ref } from 'vue'
import { pushToast } from '../../toast'
import { api } from '../sidecar-client'
import { loadAll } from './index'
import { selectedId } from './detail'

// ---------------------------------------------------------------------------
// 导入向导（用户示例集合：示例库与应用解耦）
// ---------------------------------------------------------------------------
export const importWizardOpen = ref(false)

export function openImportWizard(): void {
  importWizardOpen.value = true
}
export function closeImportWizard(): void {
  importWizardOpen.value = false
}

/** 删除用户集合示例（sidecar 侧二次校验归属）：成功后关闭详情并刷新列表 */
export async function deleteUserExample(id: string): Promise<boolean> {
  try {
    await api.deleteExample(id)
    selectedId.value = null
    await loadAll()
    pushToast('success', '示例已从你的集合中删除')
    return true
  } catch (err) {
    pushToast('error', `删除失败: ${(err as Error).message}`)
    return false
  }
}
