import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'node:path'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: 'out/main',
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/main/index.ts')
        }
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: 'out/preload',
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/preload/index.ts')
        }
      }
    }
  },
  renderer: {
    root: 'src/renderer',
    plugins: [vue(), tailwindcss()],
    build: {
      outDir: 'out/renderer',
      rollupOptions: {
        // MPA：旧渲染层（迁移期保留）与 Vue 渲染层并行构建
        input: {
          index: resolve(__dirname, 'src/renderer/index.html'),
          vue: resolve(__dirname, 'src/renderer/vue/index.html')
        }
      }
    }
  }
})
