/// <reference types="vite/client" />

// 从 preload.ts 导入 SidecarAPI 类型
import type { SidecarAPI } from '../../preload/index'

declare global {
  interface Window {
    sidecar: SidecarAPI
  }
}

export {}
