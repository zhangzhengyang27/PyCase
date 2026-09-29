// platform.ts：渲染层读取平台层的唯一入口（平台探测 + 平台差异的适配实现）。
//
// 平台由 preload 按 process.platform 写入 html[data-platform]（见 preload/index.ts），
// 组件不自行猜平台：
//   - 文案/快捷键提示 → modKeyLabel()；
//   - Windows 自绘标题栏三键 → windowControls（走类型化客户端，组件不再摸 window.sidecar）；
//   - 视觉差异（几何/窗口装饰）全在 CSS 的 data-platform 层，不进 TS。
export type Platform = 'mac' | 'win'

export function currentPlatform(): Platform {
  return document.documentElement.getAttribute('data-platform') === 'win' ? 'win' : 'mac'
}

/** 修饰键标签：mac ⌘ / win Ctrl */
export function modKeyLabel(): string {
  return currentPlatform() === 'win' ? 'Ctrl' : '⌘'
}

/** 自绘标题栏三键是否展示（mac 用原生红绿灯，不渲染自绘按钮） */
export function showsWindowControls(): boolean {
  return currentPlatform() === 'win'
}

export interface WindowControls {
  minimize(): void
  toggleMaximize(): Promise<boolean>
  close(): void
  isMaximized(): Promise<boolean>
  /** 订阅最大化状态变化；返回退订函数（App 卸载时调用） */
  onMaximizedChange(fn: (maximized: boolean) => void): () => void
}

/** 窗口控制适配：把所有平台差异收在这里（组件只认这个接口）。 */
export function createWindowControls(deps: {
  minimize: () => Promise<unknown>
  toggleMaximize: () => Promise<boolean>
  close: () => Promise<unknown>
  isMaximized: () => Promise<boolean>
  onMaximized: (fn: (maximized: boolean) => void) => () => void
}): WindowControls {
  return {
    minimize: () => void deps.minimize().catch(() => {}),
    toggleMaximize: () => deps.toggleMaximize().catch(() => false),
    close: () => void deps.close().catch(() => {}),
    isMaximized: () => deps.isMaximized().catch(() => false),
    onMaximizedChange: (fn) => deps.onMaximized(fn)
  }
}
