// store/date-run.ts：日期计算器抽屉的「运行」链路。
// 走 sidecar run_example 的可选 code 参数（adhoc 工作区，Task 7 契约），
// 按本页 run_id 过滤事件流，与 detail store 的输出面完全独立
// （不共享 appendOutput / surfaceState——两处输出语义不同，互不干扰）。
import { ref } from 'vue'
import { api, on } from '../sidecar-client'

export const runOutput = ref('')
export const runExitCode = ref<number | null>(null)
export const runBusy = ref(false)
/** 本次运行在工作区生成的图片（file:// URL，sidecar 扫描产出）——文件管道工具的产物预览源 */
export const runImages = ref<string[]>([])
/**
 * 运行上下文（`${schemaId}|${type ?? ''}`）：运行结果归属哪个页面+类型。
 * 结果区/抽屉只在上下文匹配时显示输出与产物图——运行状态是模块级 store，
 * 组件卸载（返回画廊）再重挂载（进新示例）不会自己重置，按上下文隔离才能
 * 既不串页、又让同一家族卡来回进出时保留各自的上次结果。
 */
export const runContext = ref<string | null>(null)

let currentRunId: string | null = null

export function runSnippet(id: string, code: string, context?: string): void {
  if (runBusy.value) return
  runBusy.value = true
  runOutput.value = ''
  runExitCode.value = null
  runImages.value = []
  runContext.value = context ?? `${id}|`
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
  api.stopRun(currentRunId).catch((err) => {
    runOutput.value += `[错误] 停止失败: ${(err as Error).message}\n`
  })
}

on('runOutput', (e) => {
  if (e.run_id === currentRunId) runOutput.value += e.text
})
// sidecar 运行结束前扫描工作区推送产物图（PIL/OpenCV/matplotlib）——
// 详情页运行链路有自己的订阅，这里补齐交互页链路（此前 runImages 只清空从没人写入）
on('runImages', (e) => {
  if (e.run_id !== currentRunId) return
  runImages.value = e.images || []
})
on('runFinished', (e) => {
  if (e.run_id !== currentRunId) return
  runExitCode.value = e.exit_code
  runBusy.value = false
  // 镜像 detail store：过滤在前、置空在后。清掉 run_id 意味着「无活动运行」——
  // 完成后再点停止不会误发 stopRun，迟到的 runOutput 也不会污染下一次运行的输出。
  currentRunId = null
})
