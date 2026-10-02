// CodeDrawer 接线：代码随 Tab/输入生成、复制写剪贴板、运行按钮带生成代码调 date-run。
// monaco 与 sidecar-client 都 mock（jsdom 无真实 monaco/桥；date-run 的行为已被自身 spec 覆盖）。
import { beforeEach, describe, expect, it, vi } from 'vitest'

const hoisted = vi.hoisted(() => ({
  runSnippet: vi.fn(),
  listeners: {} as Record<string, (d: unknown) => void>
}))

vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

vi.mock('../../src/sidecar-client', () => ({
  api: {
    runExample: vi.fn(async () => ({ run_id: 'r1' })),
    stopRun: vi.fn(async () => ({ status: 'terminating' as const, run_id: 'r1' }))
  },
  on: (ch: string, fn: (d: unknown) => void) => {
    hoisted.listeners[ch] = fn
    return () => {}
  }
}))

// 部分模拟 date-run：保真实 refs（runBusy/runExitCode/runOutput 仍驱动组件渲染），
// 只把 runSnippet 换成可断言的 spy——真实实现无法直接 spy 模块内导出的函数引用。
vi.mock('../../src/store/date-run', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/store/date-run')>()
  return { ...actual, runSnippet: hoisted.runSnippet }
})

import { mount } from '@vue/test-utils'
import CodeDrawer from '../date-calculator/CodeDrawer.vue'
import { activeTab, arithRows, dateA, dateB } from '../../src/store/interactive'
import { DATE_CALC_ID } from '../../src/interactive-tools'

const clipboardWrite = vi.fn<(code: string) => Promise<void>>(async () => {})
Object.assign(navigator, { clipboard: { writeText: clipboardWrite } })

beforeEach(() => {
  dateA.value = '2024-01-01'
  dateB.value = '2025-01-01'
  activeTab.value = 'diff'
  arithRows.value = [{ target: 'd1', op: '+', n: 30, unit: 'day' }]
  clipboardWrite.mockClear()
  hoisted.runSnippet.mockClear()
})

describe('CodeDrawer', () => {
  it('默认折叠；展开后容器出现', async () => {
    const w = mount(CodeDrawer)
    expect(w.find('[data-testid="drawer-run"]').exists()).toBe(false)
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    expect(w.find('[data-testid="drawer-toggle"]').attributes('aria-expanded')).toBe('true')
    expect(w.find('[data-testid="drawer-copy"]').exists()).toBe(true)
  })
  it('复制按钮写入当前生成代码并 toast', async () => {
    const w = mount(CodeDrawer)
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    await w.find('[data-testid="drawer-copy"]').trigger('click')
    expect(clipboardWrite).toHaveBeenCalledTimes(1)
    expect(String(clipboardWrite.mock.calls[0]![0])).toContain('d1 = date(2024, 1, 1)')
    expect(String(clipboardWrite.mock.calls[0]![0])).toContain('d2 = date(2025, 1, 1)')
  })
  it('运行按钮把生成代码交给 runSnippet', async () => {
    const w = mount(CodeDrawer)
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    await w.find('[data-testid="drawer-run"]').trigger('click')
    expect(hoisted.runSnippet).toHaveBeenCalledTimes(1)
    expect(hoisted.runSnippet).toHaveBeenCalledWith(DATE_CALC_ID, expect.stringContaining('d2 = date(2025, 1, 1)'))
  })
  it('Tab 切换后生成代码随之变化（diff → calendar）', async () => {
    const w = mount(CodeDrawer)
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    activeTab.value = 'calendar'
    await w.find('[data-testid="drawer-copy"]').trigger('click')
    expect(String(clipboardWrite.mock.calls[0]![0])).toContain('calendar.month(')
  })
})
