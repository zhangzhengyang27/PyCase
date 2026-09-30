// runner.ts：运行器视图域（名称搜索 / 只读预览 / 单行参数运行）。
import { computed, ref } from 'vue'
import { splitArgs } from '../utils'
import { examples } from './catalog'
import type { RunHistoryEntry } from '../types'
import {
  clearSurface,
  isRunning,
  openDetail,
  pendingBackfillTokens,
  requiredArgsMissing,
  runFromDetail,
  selectedId,
  startRun
} from './detail'

// 运行器视图（最基础的运行入口：名称搜索 / 只读预览 / 单行参数）
// ---------------------------------------------------------------------------
export const runnerSelectedId = ref<string | null>(null)
export const runnerArgsLine = ref('')
export const runnerQuery = ref('')
export const runnerHits = computed(() => {
  const q = runnerQuery.value.trim().toLowerCase()
  if (!q) return []
  return examples.value.filter((e) => e.name.toLowerCase().includes(q)).slice(0, 8)
})
export const runnerExample = computed(() => examples.value.find((e) => e.id === runnerSelectedId.value) || null)

export function selectRunnerExample(id: string): void {
  if (!examples.value.some((e) => e.id === id)) return
  runnerSelectedId.value = id
  runnerQuery.value = ''
}

export function runnerRun(): void {
  const ex = runnerExample.value
  if (!ex || isRunning.value) return
  startRun(ex.id, splitArgs(runnerArgsLine.value), 'runner')
}

export function clearRunnerOutput(): void {
  clearSurface('runner')
}

/** 历史重跑：等参数装载完成后回填记录参数再运行（ArgsForm 消费回填令牌） */
export async function rerunEntry(entry: RunHistoryEntry): Promise<void> {
  if (isRunning.value) return
  await openDetail(entry.id)
  if (selectedId.value !== entry.id) return
  pendingBackfillTokens.value = entry.args || []
  if (requiredArgsMissing.value && (entry.args || []).length === 0) return
  runFromDetail()
}
