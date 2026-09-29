// platform.ts：渲染层读取平台层的唯一入口
// 平台由 preload 按 process.platform 写入 html[data-platform]（见 preload/index.ts），
// 组件不自行猜平台；只在这里读一次并派生出文案/快捷键提示。
export type Platform = 'mac' | 'win'

export function currentPlatform(): Platform {
  return document.documentElement.getAttribute('data-platform') === 'win' ? 'win' : 'mac'
}

/** 修饰键标签：mac ⌘ / win Ctrl */
export function modKeyLabel(): string {
  return currentPlatform() === 'win' ? 'Ctrl' : '⌘'
}
