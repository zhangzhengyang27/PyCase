import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn.mjs'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './main.css'
import App from './App.vue'

// 主题初始化：与旧渲染层共用 localStorage 'app-theme' 键；
// Element Plus 暗色走 html.dark 类（dark/css-vars.css），应用令牌走 data-theme，两者同步切换
const savedTheme = localStorage.getItem('app-theme') || 'dark'
document.documentElement.setAttribute('data-theme', savedTheme)
document.documentElement.classList.toggle('dark', savedTheme === 'dark')

createApp(App).use(ElementPlus, { locale: zhCn }).mount('#app')
