// store/date-run.ts：日期计算器抽屉的「运行」链路。
// 走 sidecar run_example 的可选 code 参数（adhoc 工作区，Task 7 契约），
// 按本页 run_id 过滤事件流，与 detail store 的输出面完全独立
// （不共享 appendOutput / surfaceState——两处输出语义不同，互不干扰）。
import { ref } from 'vue'
import { api, on } from '../sidecar-client'

export const runOutput = ref('')
export const runExitCode = ref<number | null>(null)
export const runBusy = ref(false)

let currentRunId: string | null = null

export function runSnippet(id: string, code: string): void {
  if (runBusy.value) return
  runBusy.value = true
  runOutput.value = ''
  runExitCode.value = null
  api
    .runExample({ id, code })
    .then(({ run_id }) => {
      currentRunId = run_id
    })
    .catch((err) => {
      runBusy.value = false
      currentRunId = null
      runOutput.value = `[错误] ${(err as Error).message}\n`
    })
}

export function stopSnippet(): void {
  if (!currentRunId) return
  void api.stopRun(currentRunId).catch(() => {})
}

on('runOutput', (e) => {
  if (e.run_id === currentRunId) runOutput.value += e.text
})
on('runFinished', (e) => {
  if (e.run_id !== currentRunId) return
  runExitCode.value = e.exit_code
  runBusy.value = false
})
