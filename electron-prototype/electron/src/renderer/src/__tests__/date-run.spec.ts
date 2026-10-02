// date-run：runExample(code) 封装 + run_id 事件过滤。sidecar-client 整体 mock，
// 用捕获的监听器模拟事件流，不依赖 window.sidecar 桩的行为。
import { beforeEach, describe, expect, it, vi } from 'vitest'

// vi.mock 会被提升到文件顶部，但其工厂在 import 阶段才执行（早于模块体的 const 初始化），
// 因此被工厂引用的这些绑定必须经 vi.hoisted 同步提升，否则命中 TDZ。
const { listeners, runExample, stopRun } = vi.hoisted(() => {
  const listeners: Record<string, (data: unknown) => void> = {}
  const runExample = vi.fn(async () => ({ run_id: 'r1' }))
  const stopRun = vi.fn(async () => ({ status: 'terminating' as const, run_id: 'r1' }))
  return { listeners, runExample, stopRun }
})

vi.mock('../sidecar-client', () => ({
  api: {
    runExample: (...a: unknown[]) => runExample(...(a as [])),
    stopRun: (...a: unknown[]) => stopRun(...(a as []))
  },
  on: (ch: string, fn: (data: unknown) => void) => {
    listeners[ch] = fn
    return () => {}
  }
}))

import { runBusy, runExitCode, runOutput, runSnippet, stopSnippet } from '../store/date-run'
import { DATE_CALC_ID } from '../interactive-tools'

beforeEach(() => {
  runOutput.value = ''
  runExitCode.value = null
  runBusy.value = false
  runExample.mockClear()
  stopRun.mockClear()
})

describe('runSnippet', () => {
  it('带 code 调 runExample 并进入 busy', async () => {
    runSnippet(DATE_CALC_ID, "print('hi')")
    // Task 7 契约：api.runExample 收单个 params 对象（{ id, code }），不是位置参数
    await vi.waitFor(() => expect(runExample).toHaveBeenCalledWith({ id: DATE_CALC_ID, code: "print('hi')" }))
    expect(runBusy.value).toBe(true)
  })
  it('runOutput/runFinished 只接受本 run_id', async () => {
    runSnippet(DATE_CALC_ID, "print('hi')")
    await vi.waitFor(() => expect(runBusy.value).toBe(true))
    listeners.runOutput({ run_id: 'other', text: 'NOISE' })
    listeners.runOutput({ run_id: 'r1', text: 'HI\n' })
    expect(runOutput.value).toBe('HI\n')
    listeners.runFinished({ run_id: 'r1', exit_code: 0 })
    expect(runBusy.value).toBe(false)
    expect(runExitCode.value).toBe(0)
  })
  it('runExample 拒绝时落错误文本并退出 busy', async () => {
    runExample.mockRejectedValueOnce(new Error('code 超长（上限 64000 字符）'))
    runSnippet(DATE_CALC_ID, 'x')
    await vi.waitFor(() => expect(runBusy.value).toBe(false))
    expect(runOutput.value).toContain('code 超长')
  })
  it('stopSnippet 调 stopRun', async () => {
    runSnippet(DATE_CALC_ID, 'x')
    await vi.waitFor(() => expect(runBusy.value).toBe(true))
    stopSnippet()
    await vi.waitFor(() => expect(stopRun).toHaveBeenCalled())
  })
  it('runFinished 之后 stopSnippet 不再发 stopRun（run_id 已清，无活动运行）', async () => {
    runSnippet(DATE_CALC_ID, 'x')
    await vi.waitFor(() => expect(runBusy.value).toBe(true))
    listeners.runFinished({ run_id: 'r1', exit_code: 0 })
    await vi.waitFor(() => expect(runBusy.value).toBe(false))
    stopSnippet()
    expect(stopRun).not.toHaveBeenCalled()
  })
})
