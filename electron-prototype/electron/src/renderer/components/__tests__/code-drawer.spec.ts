// CodeDrawer 接线（通用化后）：代码由 props 传入、复制写剪贴板、运行按钮把
// (runId, code) 交给 date-run。monaco mock（jsdom 无真实 monaco）；date-run 部分
// mock（保真实 refs，runSnippet 换 spy——真实实现无法直接 spy 模块内导出函数）。
import { beforeEach, describe, expect, it, vi } from 'vitest'

const hoisted = vi.hoisted(() => ({
  runSnippet: vi.fn(),
  monacoCreate: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() }))
}))

vi.mock('../../monaco', () => ({
  monaco: { editor: { create: hoisted.monacoCreate } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

vi.mock('../../src/store/date-run', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/store/date-run')>()
  return { ...actual, runSnippet: hoisted.runSnippet }
})

import { mount } from '@vue/test-utils'
import CodeDrawer from '../date-calculator/CodeDrawer.vue'
import { DATE_CALC_ID } from '../../src/interactive-tools'

const clipboardWrite = vi.fn<(code: string) => Promise<void>>(async () => {})
Object.assign(navigator, { clipboard: { writeText: clipboardWrite } })

const CODE_A = 'd1 = date(2024, 1, 1)\n'
const CODE_B = 'print("changed")\n'

beforeEach(() => {
  clipboardWrite.mockClear()
  hoisted.runSnippet.mockClear()
  hoisted.monacoCreate.mockClear()
})

describe('CodeDrawer（props 化）', () => {
  it('默认折叠；展开后容器出现且 aria-expanded 同步', async () => {
    const w = mount(CodeDrawer, { props: { code: CODE_A, runId: DATE_CALC_ID } })
    expect(w.find('[data-testid="drawer-run"]').exists()).toBe(false)
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    expect(w.find('[data-testid="drawer-toggle"]').attributes('aria-expanded')).toBe('true')
    expect(w.find('[data-testid="drawer-copy"]').exists()).toBe(true)
  })
  it('复制按钮写入 props.code 并 toast', async () => {
    const w = mount(CodeDrawer, { props: { code: CODE_A, runId: DATE_CALC_ID } })
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    await w.find('[data-testid="drawer-copy"]').trigger('click')
    expect(clipboardWrite).toHaveBeenCalledTimes(1)
    expect(clipboardWrite.mock.calls[0]![0]).toBe(CODE_A)
  })
  it('运行按钮把 (runId, code) 交给 runSnippet', async () => {
    const w = mount(CodeDrawer, { props: { code: CODE_A, runId: DATE_CALC_ID } })
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    await w.find('[data-testid="drawer-run"]').trigger('click')
    expect(hoisted.runSnippet).toHaveBeenCalledTimes(1)
    expect(hoisted.runSnippet).toHaveBeenCalledWith(DATE_CALC_ID, CODE_A)
  })
  it('code prop 变化 → 编辑器 setValue（创建一次，不重建）', async () => {
    const w = mount(CodeDrawer, { props: { code: CODE_A, runId: DATE_CALC_ID } })
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    expect(hoisted.monacoCreate).toHaveBeenCalledTimes(1)
    await w.setProps({ code: CODE_B })
    expect(hoisted.monacoCreate).toHaveBeenCalledTimes(1)
    expect(hoisted.monacoCreate.mock.results[0]!.value.setValue).toHaveBeenCalledWith(CODE_B)
  })
})
