// output.ts：运行输出（v0.6 输出汇模型）
// 同一时刻至多一个运行（state.isRunning），其输出按 state.runSink 路由到
// 唯一的可见面板：detail（详情页）或 runner（运行器），不再双写。
// 包含行数限制机制，防止大量日志导致 DOM 节点爆炸、界面卡顿。

import { els, state } from './state'
import { OUTPUT_LINE_CLS, escapeHtml } from './utils'
// 运行时才调用（事件监听器内），ESM 循环依赖安全
import { downloadResultImage } from './app'

export type OutputSurface = 'detail' | 'runner'

const MAX_OUTPUT_LINES = 5000

interface SurfaceRefs {
  viewer: HTMLElement | null
  images: HTMLElement | null
  statusDot: HTMLElement | null
}

function surfaceRefs(surface: OutputSurface): SurfaceRefs {
  return surface === 'runner'
    ? { viewer: els.runnerOutputViewer, images: els.runnerOutputImages, statusDot: els.runnerStatusDot }
    : { viewer: els.detailOutputViewer, images: els.detailOutputImages, statusDot: els.detailOutputStatusDot }
}

// ---------------------------------------------------------------------------
// 行数限制（每个面板独立计数）
// ---------------------------------------------------------------------------
const _lineCount = new Map<string, number>()
const _truncated = new Map<string, boolean>()

function appendCapped(surface: OutputSurface, text: string, className = ''): void {
  const { viewer } = surfaceRefs(surface)
  if (!viewer) return
  const placeholder = viewer.querySelector('.output-placeholder')
  if (placeholder) placeholder.remove()

  let count = _lineCount.get(surface) || 0
  if (count >= MAX_OUTPUT_LINES) {
    const removeCount = Math.floor(MAX_OUTPUT_LINES * 0.1)
    for (let i = 0; i < removeCount; i++) {
      if (viewer.firstChild) viewer.removeChild(viewer.firstChild)
    }
    count -= removeCount
    if (!_truncated.get(surface)) {
      _truncated.set(surface, true)
      const notice = document.createElement('div')
      notice.className = OUTPUT_LINE_CLS.system
      notice.textContent = `[系统] 输出超过 ${MAX_OUTPUT_LINES} 行，已自动截断，仅保留最近的输出`
      viewer.insertBefore(notice, viewer.firstChild)
      count++
    }
  }

  const line = document.createElement('div')
  line.className = OUTPUT_LINE_CLS[(className || 'base') as keyof typeof OUTPUT_LINE_CLS] ?? OUTPUT_LINE_CLS.base
  line.textContent = text
  viewer.appendChild(line)
  _lineCount.set(surface, count + 1)
  // 仅当用户本就停留在底部时才自动滚底：上翻查看历史输出时不应被拽回
  const nearBottom = viewer.scrollHeight - viewer.scrollTop - viewer.clientHeight < 40
  if (nearBottom) viewer.scrollTop = viewer.scrollHeight
}

/** 清空某面板的输出并复位计数 */
export function clearSurfaceOutput(surface: OutputSurface): void {
  const { viewer } = surfaceRefs(surface)
  if (viewer) {
    viewer.innerHTML = `<div class="output-placeholder text-ink-faint text-[11px]">${
      surface === 'runner' ? '选择示例后点击「运行」，输出将实时显示在这里' : '点击「运行」，输出将实时显示在这里'
    }</div>`
    viewer.scrollTop = 0
  }
  _lineCount.set(surface, 0)
  _truncated.set(surface, false)
}

/** 设置某面板的运行状态点（idle/running/success/error） */
export function setSurfaceStatusDot(surface: OutputSurface, cls: string): void {
  const { statusDot } = surfaceRefs(surface)
  if (statusDot) statusDot.className = cls
}

// ---------------------------------------------------------------------------
// 输出写入
// ---------------------------------------------------------------------------
/** 本次运行的标准输出入口：按 runSink 路由（未指定时落详情页） */
export function appendRunOutput(text: string, className = ''): void {
  appendCapped(state.runSink || 'detail', text, className)
}

/** 详情页系统消息（保存回写提示等，与运行输出共用面板） */
export function appendDetailOutput(text: string, className = ''): void {
  appendCapped('detail', text, className)
}

// ---------------------------------------------------------------------------
// 结果图片（sidecar run_images 通知）
// ---------------------------------------------------------------------------
export function renderSurfaceImages(surface: OutputSurface, imageUrls: string[]): void {
  const { images } = surfaceRefs(surface)
  if (!images || !Array.isArray(imageUrls) || imageUrls.length === 0) return
  const items = imageUrls
    .map((url) => {
      const name = decodeURIComponent(url.split('/').pop() || 'image')
      // url 来自 sidecar 生成的 file:// URI，但输入源是可导入集合的运行目录，
      // 属性位置统一转义；name 含示例文件名，同样转义
      const safeUrl = escapeHtml(url)
      const safeName = escapeHtml(name)
      return `
        <figure class="output-image-item m-0 border border-line-subtle rounded-lg overflow-hidden bg-panel">
          <img src="${safeUrl}" alt="${safeName}" loading="lazy" class="block w-full h-[150px] object-contain bg-[#fafafa]" />
          <figcaption class="flex items-center justify-between gap-1.5 px-2 py-1 text-[11px] text-ink-mute">
            <span class="output-image-name truncate" title="${safeName}">${safeName}</span>
            <button class="output-image-download shrink-0 px-2 py-0.5 text-[11px] border border-line-subtle rounded-md bg-panel text-ink-dim cursor-pointer hover:bg-[rgba(94,106,210,0.12)] hover:text-accent" type="button" data-url="${safeUrl}" data-name="${safeName}">⬇ 下载</button>
          </figcaption>
        </figure>`
    })
    .join('')
  images.innerHTML = `
    <div class="text-[12px] font-[590] text-ink-dim mb-2">运行结果图片</div>
    <div class="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">${items}</div>`
  images.style.display = ''
  // 事件委托绑定一次：点结果图上的「下载」按钮
  if (!images.dataset.dlBound) {
    images.dataset.dlBound = '1'
    images.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('.output-image-download')
      if (!btn) return
      downloadResultImage((btn as HTMLElement).dataset.url || '', (btn as HTMLElement).dataset.name || 'image')
    })
  }
}

export function clearSurfaceImages(surface: OutputSurface): void {
  const { images } = surfaceRefs(surface)
  if (!images) return
  images.innerHTML = ''
  images.style.display = 'none'
}
