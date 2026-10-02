// sidecar-result.ts：sidecar 计算型工具的运行输出解析（W8-W11 框架件）。
// 约定：pyCode 产物把结果 JSON 包在 <<<JSON>>> / <<<END>>> 标记之间（stdout 与
// stderr 在 sidecar 已合并，标记是唯一可靠的切分方式）；标记外文本进日志区。
import type { ToolResult } from './interactive-tools'

export interface ParsedSidecarOutput {
  result: ToolResult | null
  /** 标记外的剩余输出（进度/告警行，日志区展示） */
  rest: string
}

export function parseSidecarOutput(output: string): ParsedSidecarOutput {
  const start = output.indexOf('<<<JSON>>>')
  if (start === -1) return { result: null, rest: output }
  const end = output.indexOf('<<<END>>>', start)
  const jsonText = output.slice(start + '<<<JSON>>>'.length, end === -1 ? output.length : end).trim()
  const rest = (output.slice(0, start) + (end === -1 ? '' : output.slice(end + '<<<END>>>'.length))).trim()
  try {
    const parsed = JSON.parse(jsonText) as ToolResult
    if (parsed === null || typeof parsed !== 'object') return { result: null, rest: output }
    return { result: parsed, rest }
  } catch {
    return { result: null, rest: output }
  }
}
