# 前端模块化拆分方案

> **存档**：前端重构旧计划（其范围已被 docs/redesign-plan.md 的 A/B 两轨取代）。当前事实以 [docs/redesign-plan.md] 为准；本文件保留作历史记录，不再更新。

<!-- doc-refs: skip -->

> **⚠️ 已过时，仅作存档（2026-09-11 标注）**：本文档描述的是旧 vanilla JS 渲染层
> （`renderer/app.js` + `renderer/js/*.js`）的拆分方案。该目录已随 v0.6/v0.7 渲染层
> 迁移 **整体删除**，由 Vue 3 组件体系（`src/renderer/components/` + `src/renderer/src/`）
> 取代，文中所有文件引用均不复存在。现状见 [ROADMAP.md](../ROADMAP.md) 能力矩阵。

> 当前 `electron-prototype/electron/renderer/app.js` 约 1800 行单文件，包含状态管理、
> DOM 操作、Monaco 集成、5 个主题视图、运行逻辑、参数表单、资源上传等全部逻辑。
> 本文档给出渐进式拆分方案，可按模块逐步迁移，每步都可独立验证。

## 拆分进度

| 模块 | 状态 | 行数 | 说明 |
|---|---|---|---|
| `js/utils.js` | ✅ 已完成 | 140 | 9 个纯函数（escapeHtml、图标函数、highlightCodeLine、formatFileSize） |
| `js/state.js` | ✅ 已完成 | 153 | 全局状态、THEMES 配置、isThemeView、DOM 引用（els/themeEls） |
| `js/output.js` | ✅ 已完成 | 115 | 输出面板、行数限制、截断逻辑、resetOutputCount/resetThemeOutputCount |
| `js/args-form.js` | ✅ 已完成 | 145 | 参数表单渲染、值收集、hideArgsPanel |
| `js/monaco-editor.js` | ✅ 已完成 | 163 | Monaco Editor 初始化、主题定义（linear-dark/linear-light）、事件监听 |
