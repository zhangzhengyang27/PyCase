import { createApp } from 'vue'
import './main.css'
import App from './App.vue'
import { getTestApi } from './store'

// 主题初始化：与旧渲染层共用 localStorage 'app-theme' 键（dark/light/system 三态），
// 应用令牌走 data-theme。preload 已在首帧前解析并恢复主题，这里同步 theme-color meta。
const savedTheme = localStorage.getItem('app-theme') || 'dark'
const systemDark = window.matchMedia('(prefers-color-scheme: dark)')
const resolvedTheme = savedTheme === 'system' ? (systemDark.matches ? 'dark' : 'light') : savedTheme
document.documentElement.setAttribute('data-theme', resolvedTheme)
document
  .querySelector('meta[name="theme-color"]')
  ?.setAttribute('content', resolvedTheme === 'light' ? '#f7f8f8' : '#08090a')

createApp(App).mount('#app')

// 冒烟/E2E：主进程在测试模式下给入口 URL 加 ?smoke=1，此时暴露驱动钩子
if (new URLSearchParams(window.location.search).has('smoke')) {
  ;(window as unknown as { __app: Record<string, unknown> }).__app = getTestApi()
}
