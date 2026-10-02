// store/interactive.ts：日期计算器页面状态（日期对 / 激活 Tab / 加减行）。
// 会话内记忆：切走再回来保持；返回列表只清 selectedId，不清这里。
import { ref } from 'vue'
import { selectedId } from './detail'
import { DATE_CALC_ID } from '../interactive-tools'

export type TabKey = 'diff' | 'countdown' | 'arith' | 'calendar'

export interface ArithRow {
  target: 'd1' | 'd2'
  op: '+' | '-'
  n: number
  unit: 'day' | 'week' | 'month' | 'year'
}

export const dateA = ref('2024-01-01')
export const dateB = ref('2025-01-01')
export const activeTab = ref<TabKey>('diff')
export const arithRows = ref<ArithRow[]>([{ target: 'd1', op: '+', n: 30, unit: 'day' }])

/** 打开交互工具页（selectedId 命中 interactive: 前缀时 App.vue 渲染专属页） */
export function openInteractive(id: string = DATE_CALC_ID): void {
  selectedId.value = id
}

/** 返回列表（本页无脏状态，直接清选中） */
export function closeInteractive(): void {
  selectedId.value = null
}

export function swapDates(): void {
  const t = dateA.value
  dateA.value = dateB.value
  dateB.value = t
}

// ---------------------------------------------------------------------------
// schema 驱动工具的输入值（按工具 id 分桶；会话内记忆，返回列表不清空）
// ---------------------------------------------------------------------------
import type { FieldSpec, FieldValue } from '../interactive-tools'

export const toolValues = ref<Record<string, Record<string, FieldValue>>>({})

/** 取工具输入桶：首次按字段 defaults 初始化；之后恒返回同一对象（v-model 直接改写） */
export function toolValueOf(id: string, fields: FieldSpec[]): Record<string, FieldValue> {
  if (!toolValues.value[id]) {
    const init: Record<string, FieldValue> = {}
    for (const f of fields) init[f.key] = f.default
    toolValues.value[id] = init
  }
  return toolValues.value[id]
}
