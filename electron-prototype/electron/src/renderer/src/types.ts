// types.ts：渲染层共享类型（原 state.ts 的数据模型部分；视图编排代码已由 Vue 渲染层取代）

/** 单条 HIGH 风险明细（sidecar risk_findings，运行前确认弹窗展示用） */
export interface RiskFinding {
  description: string
  category: string
}

export interface ExampleItem {
  id: string
  name: string
  category: string
  path: string
  code?: string
  description?: string
  tags?: string[]
  args?: string[]
  title?: string
  quality_score?: number
  risk_high?: boolean
  /** 可运行性派生状态：runnable / missing_deps / empty / broken / risky */
  run_status?: string
  /** HIGH 风险明细（仅高危条目携带） */
  risk_findings?: RiskFinding[]
  /** 所属集合名（📦 前缀已剥离；内置库为集合文件 name 字段） */
  collection?: string
  /** 是否属于用户集合（可删除；内置集合受保护） */
  user_collection?: boolean
  /** 原始仓库内相对目录（内置库 JSON 的 dir 字段，如 'tools/utility-crawlers'）；工具箱分组用 */
  source_dir?: string
  _importTags?: string[]
}

export interface RunHistoryEntry {
  ts: string
  id: string
  name: string
  args: string[]
  duration_ms: number
  exit_code: number
  ok: boolean
}
