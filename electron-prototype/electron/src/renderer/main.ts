import { createApp } from 'vue'
import './main.css'
import App from './App.vue'
import { getTestApi } from './src/store/index'

// 三层绑定初始化：与 preload 同一套口径（preload 已在首帧前设好，这里是幂等兜底 +
// theme-color meta 同步）。平台由 preload 按 process.platform 写入，渲染层不猜平台。
const savedTheme = localStorage.getItem('app-theme') || 'dark'
const systemDark = window.matchMedia('(prefers-color-scheme: dark)')
const resolvedTheme = savedTheme === 'system' ? (systemDark.matches ? 'dark' : 'light') : savedTheme
const rootEl = document.documentElement
rootEl.setAttribute('data-theme', resolvedTheme)
if (!rootEl.hasAttribute('data-platform')) {
  // 只有 preload 完全没跑成才走到这里：兜底不能一律写 mac——
  // Windows 上会把整层平台几何（自绘标题栏/行高/选中语义）错配成 macOS，
  // 而且因为"猜对了 macOS"，这个错在 mac 上永远看不出来。
  rootEl.setAttribute('data-platform', /Windows/i.test(navigator.userAgent) ? 'win' : 'mac')
}
if (!rootEl.hasAttribute('data-accent')) {
  rootEl.setAttribute('data-accent', localStorage.getItem('app-accent') === 'brand' ? 'brand' : 'system')
}
// theme-color 取窗口底色令牌（不留字面色值，避免与 token 漂移）
const metaEl = document.querySelector('meta[name="theme-color"]')
metaEl?.setAttribute('content', getComputedStyle(rootEl).getPropertyValue('--bg-window').trim())

createApp(App).mount('#app')

// 冒烟/E2E：主进程在测试模式下给入口 URL 加 ?smoke=1，此时暴露驱动钩子
if (new URLSearchParams(window.location.search).has('smoke')) {
  ;(window as unknown as { __app: Record<string, unknown> }).__app = getTestApi()
}
