// assets.ts：资源面板域（上传 / 列举 / 删除 / 结果图片下载）。
//
// 资源落在示例运行工作区内（契约 §4.2：资源与运行产物同处工作区，基线刷新不删）。
import { ref } from 'vue'
import { pushToast } from '../../toast'
import { api } from '../sidecar-client'
import { selectedId } from './detail'

export interface AssetInfo {
  filename: string
  size: number
  modified: number
  is_image: boolean
}

export const assets = ref<AssetInfo[]>([])
export const assetsLoading = ref(false)

// 资源上传 / 列举 / 删除
// ---------------------------------------------------------------------------
export async function loadAssets(id: string): Promise<void> {
  assetsLoading.value = true
  try {
    const result = (await api.listAssets(id)) as { assets?: AssetInfo[] }
    if (selectedId.value === id) assets.value = result.assets || []
  } catch {
    if (selectedId.value === id) assets.value = []
  } finally {
    assetsLoading.value = false
  }
}

export async function uploadAssets(id: string, files: File[]): Promise<void> {
  for (const file of files) {
    if (file.size > 15 * 1024 * 1024) {
      pushToast('info', `${file.name} 超过 15MB 限制`)
      continue
    }
    if (file.name.toLowerCase().endsWith('.py') || file.name.toLowerCase() === 'requirements.txt') {
      pushToast('info', `${file.name} 与示例脚本/依赖清单冲突，已拒绝`)
      continue
    }
    try {
      const buffer = await file.arrayBuffer()
      let binary = ''
      const bytes = new Uint8Array(buffer)
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
      await api.uploadAsset({ exampleId: id, fileName: file.name, data: btoa(binary) })
    } catch (err) {
      pushToast('error', `上传 ${file.name} 失败: ${(err as Error).message}`)
    }
  }
  await loadAssets(id)
}

export async function deleteAsset(filename: string): Promise<void> {
  if (!selectedId.value) return
  try {
    const result = (await api.deleteAsset({ exampleId: selectedId.value, fileName: filename })) as { assets?: AssetInfo[] }
    assets.value = result.assets || []
  } catch (err) {
    pushToast('error', `删除失败: ${(err as Error).message}`)
  }
}

export async function downloadImage(url: string, name: string): Promise<void> {
  try {
    const res = (await api.downloadResultImage(url, name)) as { canceled?: boolean; error?: string }
    if (res && res.error) pushToast('error', `下载失败：${res.error}`)
  } catch (err) {
    pushToast('error', `下载失败：${(err as Error).message}`)
  }
}




// ---------------------------------------------------------------------------
// 测试钩子（资源面板）：由 store/index.ts 的 getTestApi 组合成 window.__app
// ---------------------------------------------------------------------------
export function assetsTestHooks(): Record<string, unknown> {
  return {
    assets: () => assets.value,
    // 资源链路走查：走真实上传/删除（渲染层 → 客户端 → 主进程 → sidecar → 工作区）
    uploadAssets: (id: string, files: File[]) => uploadAssets(id, files),
    deleteAsset: (filename: string) => deleteAsset(filename)
  }
}
