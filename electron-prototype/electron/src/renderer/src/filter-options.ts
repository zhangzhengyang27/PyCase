// filter-options.ts：画廊筛选维度选项目录（纯数据，无 DOM / 无 store 依赖）。
//
// 原先内联在 FilterSidebar.vue。筛选栏改为工具栏下拉后，选项目录下沉到此纯模块：
// BrowseToolbar 据此渲染 <option>，单测可直接断言选项顺序与文案，无需挂载组件。
import type { RunnableFilter } from './filter-engine'

/** 可运行性（代码体检派生状态）——label + 说明，与旧侧栏同口径。 */
export interface RunnableOption {
  key: RunnableFilter
  label: string
  hint?: string
}

export const RUNNABLE_OPTIONS: readonly RunnableOption[] = [
  { key: 'all', label: '全部' },
  { key: 'runnable', label: '可运行', hint: '静态检查通过的推定状态' },
  { key: 'missing_deps', label: '缺依赖', hint: '依赖的第三方库在共享环境中缺失' },
  { key: 'empty', label: '空壳', hint: '去除 docstring 后没有有效代码' },
  { key: 'broken', label: '语法损坏', hint: '代码存在语法错误' },
  { key: 'risky', label: '高危', hint: '含高危操作，运行前需确认' }
]

/** 质量分下限档位（0 = 不筛）。 */
export interface QualityOption {
  min: number
  label: string
}

export const QUALITY_OPTIONS: readonly QualityOption[] = [
  { min: 0, label: '全部' },
  { min: 90, label: '≥90' },
  { min: 80, label: '≥80' },
  { min: 60, label: '≥60' }
]

/** 运行状态（本机运行历史派生，与「可运行性」互补）。 */
export type RunStatusKey = 'all' | 'ok' | 'failed' | 'never'

export interface RunStatusOption {
  key: RunStatusKey
  label: string
}

export const RUN_STATUS_OPTIONS: readonly RunStatusOption[] = [
  { key: 'all', label: '全部' },
  { key: 'ok', label: '成功过' },
  { key: 'failed', label: '失败过' },
  { key: 'never', label: '未运行' }
]
