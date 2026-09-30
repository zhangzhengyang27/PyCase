// ESLint 扁平配置（M6-1）：渲染层/主进程/预加载 + 仓库根 mjs 测试。
//
// 规则取向：推荐集为底 + 三条硬约束（审计 C5 的三项诉求）：
//   1. no-explicit-any：any 归零（配合 tsconfig 的 noImplicitAny）；
//   2. no-unused-vars / no-undef：死变量与未声明全局；
//   3. vue 必需规则集：SFC 模板的语义错误（键缺失、v-for key 等）。
// 格式化归 Prettier，不在这里重复（避免两套规则互相打架）。
import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
  { ignores: ['out/**', 'dist/**', 'sidecar-dist/**', 'node_modules/**', 'build-pyinstaller/work/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.{ts,vue}'],
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      parserOptions: { parser: tseslint.parser, extraFileExtensions: ['.vue'], sourceType: 'module' }
    },
    rules: {
      // 审计 C5：any 归零（显式 any 与隐式 any 都要挡）
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-empty': ['error', { allowEmptyCatch: true }],
      // Vue 模板里 v-html 属安全面：出现即人工复核（当前仓库应无）
      'vue/no-v-html': 'error'
    }
  },
  {
    // 主进程/预加载：Electron 的 Node 侧全局
    files: ['src/main/**/*.ts', 'src/preload/**/*.ts'],
    languageOptions: { globals: { ...globals.node } }
  },
  {
    // 走查探针里的 executeJavaScript 字符串是"注入的浏览器代码"，不是本进程代码
    files: ['src/main/index.ts'],
    rules: { 'no-undef': 'off' }
  }
]
