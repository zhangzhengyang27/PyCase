// tool-manuals.ts：工具手册页的路由与数据访问（W7 手册页基座）。
// 手册内容在构建期由 scripts/gen_tool_manuals.py 生成（tool-manuals.json），
// 运行时只读这份静态数据——页面零 sidecar 依赖、即开即渲染。
import { computed, reactive } from 'vue'
import manualsJson from './tool-manuals.json'
import { examples } from './store/catalog'
import { selectedId } from './store/detail'
import type { VExample } from './store/catalog'

export const MANUAL_PREFIX = 'manual:'

export function isManualId(id: string | undefined | null): boolean {
  return !!id && id.startsWith(MANUAL_PREFIX)
}

/** manual:<exampleId> → exampleId（非 manual id 返回 null） */
export function manualExampleId(id: string | undefined | null): string | null {
  return isManualId(id) ? id!.slice(MANUAL_PREFIX.length) : null
}

export interface ManualEntry {
  title: string
  summary: string
  usage: string
  params: Array<{
    flag: string
    type?: string
    default?: unknown
    help?: string
    action?: string
    nargs?: string
    positional?: boolean
  }>
  notes?: string[]
}

const DATA = manualsJson as { comment: string; manuals: Record<string, ManualEntry> }

/** 手册数据（reactive：工具目录变化时标题等回填自动更新） */
export const manualStore = reactive({
  entries: DATA.manuals as Record<string, ManualEntry>
})

export function manualFor(exampleId: string): ManualEntry | undefined {
  return manualStore.entries[exampleId]
}

/** 该工具是否有手册页（DetailPage 头部「手册」入口的显示条件） */
export function hasManual(exampleId: string | null | undefined): boolean {
  return !!exampleId && exampleId in manualStore.entries
}

export function openManual(exampleId: string | null | undefined): void {
  if (!exampleId) return
  selectedId.value = `${MANUAL_PREFIX}${exampleId}`
}

/** 手册页当前对应的目录条目（标题/标签等实时元数据；不在目录池时为 null） */
export const manualExample = computed<VExample | null>(() => {
  const exId = manualExampleId(selectedId.value)
  return exId ? (examples.value.find((e) => e.id === exId) ?? null) : null
})
