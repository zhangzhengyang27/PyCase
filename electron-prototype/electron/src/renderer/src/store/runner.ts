// runner.ts：运行器视图域（名称搜索 / 只读预览 / 单行参数运行）。
import { computed, ref } from 'vue'
import { pushToast } from '../../toast'
import { splitArgs } from '../utils'
import { examples } from './catalog'
import type { RunHistoryEntry } from '../types'
import { api } from '../sidecar-client'
import type { ExampleDetail } from '../../../../../shared/protocol'
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
/** 只读预览的源码：契约 v2 起列表项不含 code，按 id 经 get_example 单独拉取 */
export const runnerCode = ref('')
// 源码请求序号：切换/清空选中项时，先发后到的响应一律丢弃
let _runnerSeq = 0

/**
 * 拉取只读预览源码（与详情页同一口径：源码只认 get_example）。
 * 过期响应丢弃；失败不静默（置空 + toast），避免渲染成「示例是空的」。
 */
async function loadRunnerCode(id: string): Promise<void> {
  const seq = ++_runnerSeq
  runnerCode.value = ''
  try {
    const detail: Partial<ExampleDetail> | null = await api.getExample(id)
    if (seq !== _runnerSeq || runnerSelectedId.value !== id) return
    runnerCode.value = detail?.code ?? ''
  } catch (err) {
    if (seq !== _runnerSeq || runnerSelectedId.value !== id) return
    console.error('[runner] 加载源码失败:', err)
    pushToast('error', `加载源码失败: ${(err as Error).message}`)
    runnerCode.value = ''
  }
}

export function selectRunnerExample(id: string): void {
  if (!examples.value.some((e) => e.id === id)) return
  runnerSelectedId.value = id
  runnerQuery.value = ''
  void loadRunnerCode(id)
}

/** 清空运行器选中项（含预览源码）：递增序号让在途响应失效 */
export function clearRunnerSelection(): void {
  _runnerSeq++
  runnerSelectedId.value = null
  runnerCode.value = ''
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
