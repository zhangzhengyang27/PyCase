// assets.ts：详情页资源管理（上传 / 列表 / 删除）
// 上传到示例运行目录，脚本可直接按文件名引用处理；对全部示例开放。
// 依赖：els（state.ts）、escapeHtml/formatFileSize（utils.ts）、api（sidecar-client.ts）

import { els } from './state'
import { escapeHtml, formatFileSize } from './utils'
import { api } from './sidecar-client'

// ---------------------------------------------------------------------------
// 刷新详情页示例的资源列表
// ---------------------------------------------------------------------------
export async function refreshDetailAssets(id: string): Promise<void> {
  if (!els.detailAssetsList) return
  try {
    const res = await api.listAssets(id)
    const assets = res.assets || []
    if (els.detailAssetsCount) {
      els.detailAssetsCount.textContent = assets.length ? `(${assets.length})` : ''
    }
    if (!assets.length) {
      els.detailAssetsList.innerHTML = '<div class="assets-empty text-ink-mute text-[13px] py-2">尚未上传资源</div>'
      return
    }
    const imgs = assets.filter((a) => a.is_image)
    const docs = assets.filter((a) => !a.is_image)
    const row = (a, icon) => `
      <div class="asset-item flex items-center gap-2 px-2 py-1.5 rounded-md text-[13px] hover:bg-[rgba(127,127,127,0.08)]">
        <span class="asset-icon">${icon}</span>
        <span class="asset-name flex-1 truncate" title="${escapeHtml(a.filename)}">${escapeHtml(a.filename)}</span>
        <span class="asset-size text-ink-mute text-[11px] shrink-0">${formatFileSize(a.size)}</span>
        <button class="asset-del bg-transparent border-0 cursor-pointer opacity-55 text-[13px] px-1 py-0.5 shrink-0 hover:opacity-100" data-file="${escapeHtml(a.filename)}">🗑</button>
      </div>`
    els.detailAssetsList.innerHTML =
      (imgs.length ? `<div class="assets-group text-[11px] text-ink-mute mt-2 mb-1">图片</div>${imgs.map((a) => row(a, '🖼️')).join('')}` : '') +
      (docs.length ? `<div class="assets-group text-[11px] text-ink-mute mt-2 mb-1">文档</div>${docs.map((a) => row(a, '📄')).join('')}` : '')
    els.detailAssetsList.querySelectorAll('.asset-del').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation()
        const file = (btn as HTMLElement).dataset.file
        if (!file || !confirm(`删除资源 ${file}？`)) return
        try {
          await api.deleteAsset({ id, filename: file } as any)
          refreshDetailAssets(id)
        } catch (err) {
          alert(`删除失败: ${(err as any).message}`)
        }
      })
    })
  } catch (err) {
    els.detailAssetsList.innerHTML = '<div class="assets-empty text-ink-mute text-[13px] py-2">资源列表加载失败</div>'
  }
}

// ---------------------------------------------------------------------------
// 读取文件为 Base64 字符串
// ---------------------------------------------------------------------------
export function readFileAsBase64(file): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const b64 = String(reader.result).split(',')[1] || ''
      resolve(b64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// ---------------------------------------------------------------------------
// 上传资源
// ---------------------------------------------------------------------------
export async function uploadDetailAssets(id: string, files: File[]): Promise<void> {
  for (const file of files) {
    try {
      const b64 = await readFileAsBase64(file)
      await api.uploadAsset({ exampleId: id, fileName: file.name, data: b64 })
    } catch (err) {
      alert(`上传 ${file.name} 失败: ${(err as any).message}`)
    }
  }
  refreshDetailAssets(id)
}
