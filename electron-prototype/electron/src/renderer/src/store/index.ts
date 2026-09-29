// store/index.ts：应用状态层的组合根。
//
// 分域（单向依赖，无环）：
//   prefs（持久化用户数据）
//     ← catalog（示例目录/筛选/浏览）
//       ← detail（详情/参数/运行生命周期）
//         ← runner / assets / ai（各自的视图域）
//       ← import（导入向导，删集合后重新加载）
//   env（环境与全局层，独立）
//
// 本文件只做两件事：启动装载（loadAll）与测试钩子组合（getTestApi）。
// 组件按需从具体域导入，不从这里转口（避免又长出一个单体）。
import { api } from '../sidecar-client'
import {
  applyViewPrefs,
  catalogTestHooks,
  examples,
  loadExamples,
  loading,
  loadError
} from './catalog'
import { detailTestHooks } from './detail'
import { assetsTestHooks } from './assets'
import { envTestHooks } from './env'
import { applyFavorites, applyHistory, applyRunPrefs, applySafety } from './prefs'

/**
 * 启动装载：并行读持久化数据（收藏/历史/视图偏好/安全偏好/运行偏好）+ 示例列表。
 * 各域的存储格式只在 prefs/catalog 内解析，这里只做编排与错误收敛。
 */
export async function loadAll(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    const [history, favs, prefs, safety, runPrefs] = await Promise.all([
      api.storeGet('history').catch(() => null),
      api.storeGet('favorites').catch(() => null),
      api.storeGet('viewPrefs').catch(() => null),
      api.storeGet('safetyPrefs').catch(() => null),
      api.storeGet('runPrefs').catch(() => null)
    ])
    applyHistory(history)
    applyFavorites(favs)
    applyViewPrefs(prefs)
    applySafety(safety)
    applyRunPrefs(runPrefs)
    await loadExamples()
  } catch (err) {
    loadError.value = (err as Error).message
    examples.value = []
  } finally {
    loading.value = false
  }
}

// ---------------------------------------------------------------------------
// 冒烟 / E2E 测试钩子：入口 HTML 带 ?smoke=1 时由 main.ts 挂到 window.__app，
// 主进程的 runSmokeTest / runE2ETest 借此驱动 Vue 应用（生产入口不注入）。
// 各域自带钩子（域内测试也直接用它），这里只做扁平组合——钩子键名与主进程探针的
// executeJavaScript 字符串是同一份约定，键名变更必须同步改探针。
// ---------------------------------------------------------------------------
export function getTestApi(): Record<string, unknown> {
  return {
    ...catalogTestHooks(),
    ...detailTestHooks(),
    ...assetsTestHooks(),
    ...envTestHooks()
  }
}
