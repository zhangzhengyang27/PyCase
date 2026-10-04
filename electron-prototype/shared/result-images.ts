// result-images.ts：运行产物图的协议 URL 助手（main 进程；纯函数便于测试）。
//
// 为什么需要这个协议：sidecar 推来的 run_images 是 file:// URI，而 dev 模式渲染层
// 跑在 http://localhost（vite dev server）上——Chromium webSecurity 禁止 http 页面
// 加载 file:// 子资源，<img> 全部碎图（打包态 loadFile 的 file:// origin 反而能加载，
// 所以只有 dev 可见此问题）。主进程在转发 run_images 事件时把 file:// 统一改写成
// pycase-img:// 特权协议，由 protocol.handle 代理读盘（白名单：示例缓存目录 + 图片扩展名）。
export const IMG_SCHEME = 'pycase-img'

const SCHEME_PREFIX = `${IMG_SCHEME}://`

/** file:// URI → pycase-img:// URL（路径整体 encodeURIComponent，空格/中文/引号全安全）；非 file:// 原样返回 */
export function fileToImgSchemeUrl(fileUri: string): string {
  if (!fileUri.startsWith('file://')) return fileUri
  // Node fileURLToPath 之外自行解码：file URI 的 pathname 已是百分号编码
  const raw = decodeURIComponent(new URL(fileUri).pathname)
  return SCHEME_PREFIX + encodeURIComponent(raw)
}

/** pycase-img:// URL → 绝对路径；非本协议返回 null */
export function imgSchemeToPath(url: string): string | null {
  if (!url.startsWith(SCHEME_PREFIX)) return null
  try {
    return decodeURIComponent(url.slice(SCHEME_PREFIX.length))
  } catch {
    return null
  }
}
