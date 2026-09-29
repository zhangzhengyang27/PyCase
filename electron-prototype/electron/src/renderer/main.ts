import { createApp } from 'vue'
import './main.css'
import App from './App.vue'
import { getTestApi } from './store'

// 三层绑定初始化：与 preload 同一套口径（preload 已在首帧前设好，这里是幂等兜底 +
// theme-color meta 同步）。平台由 preload 按 process.platform 写入，渲染层不猜平台。
const savedTheme = localStorage.getItem('app-theme') || 'dark'
const systemDark = window.matchMedia('(prefers-color-scheme: dark)')
const resolvedTheme = savedTheme === 'system' ? (systemDark.matches ? 'dark' : 'light') : savedTheme
const rootEl = document.documentElement
rootEl.setAttribute('data-theme', resolvedTheme)
if (!rootEl.hasAttribute('data-platform')) rootEl.setAttribute('data-platform', 'mac')
if (!rootEl.hasAttribute('data-accent')) {
  rootEl.setAttribute('data-accent', localStorage.getItem('app-accent') === 'brand' ? 'brand' : 'system')
}
document
  .querySelector('meta[name="theme-color"]')
  ?.setAttribute('content', resolvedTheme === 'light' ? '#ffffff' : '#1e1e1e')

createApp(App).mount('#app')

// 冒烟/E2E：主进程在测试模式下给入口 URL 加 ?smoke=1，此时暴露驱动钩子
if (new URLSearchParams(window.location.search).has('smoke')) {
  ;(window as unknown as { __app: Record<string, unknown> }).__app = getTestApi()
}
