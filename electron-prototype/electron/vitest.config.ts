// vitest.config.ts：Vue 组件渲染层测试（.vue SFC）专用运行器。
//
// 为什么单独有这份配置、而不是复用 electron.vite.config.ts？
//   - electron.vite.config 描述的是「应用怎么打包」：三个 target（main/preload/renderer）、
//     产物目录、externalize 插件。测试只关心 renderer 的 .vue 编译，混在一起会让
//     改打包配置时误伤测试，反之亦然。
//   - 但插件必须一致：这里同样用 @vitejs/plugin-vue，因此组件在测试中的编译结果
//     与真实构建走同一条 SFC 编译链（不是另起一套转译），测试才有保真度。
//
// 与仓库根 tests/*.mjs 的分工：
//   - tests/*.mjs（node --test + tests/renderer-loader.mjs）：纯逻辑模块（filter-engine /
//     utils / overview / store），零 bundler，直接跑 TS 源码；
//   - 本配置：需要 SFC 编译 + DOM 的组件测试（src/renderer/components/__tests__/*.spec.ts）。
//   两者互补，不重复。
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // Vue 运行时特性开关：不显式声明时 SFC 编译产物会留下未替换的全局常量引用。
  define: {
    __VUE_OPTIONS_API__: 'true',
    __VUE_PROD_DEVTOOLS__: 'false',
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false'
  },
  test: {
    environment: 'jsdom',
    // 组件测试与组件同目录（__tests__/），符合 Vitest 惯例，避免再开一个顶层 tests/。
    include: ['src/renderer/components/__tests__/**/*.spec.ts'],
    // 每个测试文件独立环境；全局桩（window.sidecar / matchMedia）集中在这里。
    setupFiles: ['./vitest.setup.ts'],
    globals: false,
    restoreMocks: true,
    // 组件里没有 @apply / @tailwind，无需 Tailwind 插件；关掉 CSS 处理更快。
    css: false
  }
})
