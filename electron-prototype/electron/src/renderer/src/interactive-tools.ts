// interactive-tools.ts：交互工具注册表——不是可运行 Python 示例，是应用内交互页的
// 工具箱门面。不进内置库 JSON（避免污染可运行率 / 守卫 / sidecar 文件装载），
// 由 catalog 合并进工具池：参与搜索与收藏（客户端匹配），恒置顶展示。
//
// 两种页面形态：
//   - 专属页（如日期计算器）：复杂布局，仅注册卡片；
//   - schema 驱动页（InteractiveToolSchema）：表单 + compute + pyCode 三件套，
//     由 InteractiveToolPage 统一渲染。新工具只需往 toolSchemas 里注册一个条目。
import { computed, reactive } from 'vue'
import type { VExample } from './store/catalog'
import { TOOL_SCHEMAS } from './tool-schemas'

export const INTERACTIVE_PREFIX = 'interactive:'
export const DATE_CALC_ID = `${INTERACTIVE_PREFIX}date-calculator`
/** 工具箱「交互工具」分组 key（ToolboxView 分组与 section-icons 图标映射共用，防字符串漂移） */
export const INTERACTIVE_GROUP_KEY = 'interactive'

export function isInteractiveId(id: string | undefined | null): boolean {
  return !!id && id.startsWith(INTERACTIVE_PREFIX)
}

// ---------------------------------------------------------------------------
// schema 驱动工具的类型（设计见 docs/interactive-tools-plan.md §4.1；
// color 字段类型按 YAGNI 暂不实现，首个需要它的工具落地时再补）
// ---------------------------------------------------------------------------
export type FieldType = 'text' | 'textarea' | 'number' | 'select' | 'checkbox'
export type FieldValue = string | number | boolean | undefined

export interface FieldSpec {
  key: string
  label: string
  type: FieldType
  default?: string | number | boolean
  options?: Array<{ value: string; label: string }> // 仅 select
  placeholder?: string
  required?: boolean
  width?: 'full' | 'half'
  help?: string
}

export interface ToolResult {
  /** 大数字主结果 */
  primary?: { value: string; unit?: string }
  /** 键值行列表（copy=true 时行尾给复制按钮语义，当前仅展示层约定） */
  rows?: Array<{ label: string; value: string; copy?: boolean }>
  /** 大段文本结果（折行文本 / TOC / diff 等，等宽展示） */
  text?: string
  /** 批量生成结果（逐行可复制） */
  list?: string[]
  /** 输入不合法的引导文案（出现时不渲染其他结果） */
  error?: string
}

export interface InteractiveToolSchema {
  id: string
  title: string
  description: string
  tags: string[]
  fields: FieldSpec[]
  /** 前端计算型必填：输入 → 结构化结果（纯函数，输入缺失时返回 error 引导） */
  compute?: (v: Record<string, FieldValue>) => ToolResult
  /** 计算位置：frontend（默认，compute 必填）| sidecar（页面只采集，结果由运行输出承担） */
  computeVia?: 'frontend' | 'sidecar'
  /** 代码抽屉模板（纯函数拼接，产物可直接 python3 运行，输出与页面结果互证） */
  pyCode: (v: Record<string, FieldValue>) => string
}

// ---------------------------------------------------------------------------
// 注册表：专属卡片 + schema 派生卡片
// ---------------------------------------------------------------------------
const DATE_CARD: VExample = {
  id: DATE_CALC_ID,
  name: 'date-calculator',
  category: 'tools',
  path: '',
  title: '日期计算器',
  description: '任选起止日期，即时计算间隔、正倒计时、日期加减与日历跨度，附等价 Python 代码。',
  tags: ['日期', '交互工具']
}

/** schema 注册点（reactive——注册即反映到工具池）；内置三工具来自 tool-schemas.ts */
export const interactiveToolSchemas = reactive<InteractiveToolSchema[]>([...TOOL_SCHEMAS])

function schemaToCard(s: InteractiveToolSchema): VExample {
  return {
    id: s.id,
    name: s.id.slice(INTERACTIVE_PREFIX.length),
    category: 'tools',
    path: '',
    title: s.title,
    description: s.description,
    tags: [...s.tags, '交互工具']
  }
}

/** 工具池门面（响应式）：专属卡 + schema 派生卡；catalog 合并时以 .value 消费 */
export const interactiveToolItems = computed<VExample[]>(() => [DATE_CARD, ...interactiveToolSchemas.map(schemaToCard)])

export function getToolSchema(id: string): InteractiveToolSchema | undefined {
  return interactiveToolSchemas.find((s) => s.id === id)
}
