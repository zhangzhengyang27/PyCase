// 详情页源码装载的边界与错误路径探针（第二层 QA，独立于 detail.spec.ts 的护栏）。
//
// 与 detail.spec.ts 的分工：那份文件已覆盖「源码来自 get_example」的主干与工程师写的
// 7 条护栏；这一份专攻**工程师没覆盖到的角度**——空/异常回包、多方竞态、保存后重载、
// 运行器清空、占位串的唯一合法场景。手法刻意与 detail.spec.ts 不同（延迟更长、
// 三方切换、同 id 重复打开），避免「同一手法跑两遍」的假独立。
import { describe, expect, it, afterEach, beforeEach, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'

import MonacoEditor from '../MonacoEditor.vue'
import { examples, type VExample } from '../../src/store/catalog'
import {
  argsError,
  argsLoading,
  confirmPrompt,
  currentArgs,
  isDirty,
  onEditorContentChanged,
  openDetail,
  originalCode,
  registerEditor,
  resolveConfirm,
  retryParseArgs,
  saveExample,
  saving,
  selectedId,
  surfaceState
} from '../../src/store/detail'
import { clearRunnerSelection, runnerCode, runnerSelectedId, selectRunnerExample } from '../../src/store/runner'
import { toasts } from '../../toast'
import { applyMonacoTheme } from '../../monaco'

const PLACEHOLDER = '# 在画廊或工具箱中选择示例查看与编辑代码\n'

// 与 detail.spec.ts 同形的 Monaco 桩（有状态：create 用 options.value 初始化）。
const h = vi.hoisted(() => {
  const state = { value: '', listeners: [] as Array<() => void> }
  const fakeEditor = {
    getValue: vi.fn(() => state.value),
    setValue: vi.fn((v: string) => {
      state.value = v
    }),
    onDidChangeModelContent: vi.fn((cb: () => void) => {
      state.listeners.push(cb)
    }),
    dispose: vi.fn()
  }
  const create = vi.fn((_el: unknown, opts: Record<string, unknown>) => {
    state.value = typeof opts.value === 'string' ? opts.value : ''
    return fakeEditor
  })
  return { state, fakeEditor, create }
})

vi.mock('../../monaco', () => ({
  monaco: { editor: { create: h.create } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'pycase-dark'
}))

function resetMonaco(): void {
  h.state.value = ''
  h.state.listeners = []
  h.create.mockImplementation((_el: unknown, opts: Record<string, unknown>) => {
    h.state.value = typeof opts.value === 'string' ? opts.value : ''
    return h.fakeEditor
  })
  h.fakeEditor.getValue.mockImplementation(() => h.state.value)
  h.fakeEditor.setValue.mockImplementation((v: string) => {
    h.state.value = v
  })
  h.fakeEditor.onDidChangeModelContent.mockImplementation((cb: () => void) => {
    h.state.listeners.push(cb)
  })
}

function makeExample(over: Partial<VExample> = {}): VExample {
  return {
    id: 't1',
    name: 'alpha.py',
    category: 'topics',
    path: 'topics/alpha.py',
    title: 'Alpha',
    tags: [],
    quality_score: 90,
    run_status: 'runnable',
    _tagsAll: [],
    ...over
  }
}

const wrappers: VueWrapper[] = []

beforeEach(() => {
  currentArgs.value = []
  argsLoading.value = false
  argsError.value = ''
  confirmPrompt.value = null
  examples.value = []
  selectedId.value = null
  originalCode.value = ''
  isDirty.value = false
  saving.value = false
  toasts.value = []
  clearRunnerSelection()
  surfaceState('detail').lines = []
  surfaceState('detail').dot = 'idle'
  resetMonaco()
})

afterEach(() => {
  for (const w of wrappers.splice(0)) w.unmount()
  document.body.innerHTML = ''
})

/** 挂一个被延迟控制的 get_example：resolve 由测试手动驱动。 */
function deferGetExample(): { resolve: (v: unknown) => void; calls: string[] } {
  const calls: string[] = []
  const pending: Array<(v: unknown) => void> = []
  vi.mocked(window.sidecar.getExample).mockImplementation(((id: string) => {
    calls.push(id)
    return new Promise<unknown>((resolve) => pending.push(resolve))
  }) as never)
  return { resolve: (v: unknown) => pending.shift()?.(v), calls }
}

// ===========================================================================
describe('C1 · get_example 的空/异常回包（编辑器不得被误导成「没选示例」）', () => {
  it('返回 null 时源码置空、不抛错，且 Monaco 不回落占位串', async () => {
    vi.mocked(window.sidecar.getExample).mockResolvedValue(null as never)
    examples.value = [makeExample({ id: 't1' })]

    await openDetail('t1')
    await flushPromises()

    expect(selectedId.value).toBe('t1')
    expect(originalCode.value).toBe('')
    expect(isDirty.value).toBe(false)
    // 关键：已选中 → 编辑器必须空白，绝不能是「请选择示例」占位串
    const w = mount(MonacoEditor)
    wrappers.push(w)
    expect(h.create.mock.calls[0][1].value).toBe('')
    expect(h.create.mock.calls[0][1].value).not.toBe(PLACEHOLDER)
  })

  it('返回对象但 code 为 undefined 时同上（不把 undefined 写进编辑器）', async () => {
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 't1', name: 'alpha.py' } as never)
    examples.value = [makeExample({ id: 't1' })]

    await openDetail('t1')
    await flushPromises()

    expect(originalCode.value).toBe('')
    expect(typeof originalCode.value).toBe('string')
  })

  it('返回 code 为空串时不误判为「加载失败」，也不弹 toast', async () => {
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 't1', code: '' } as never)
    examples.value = [makeExample({ id: 't1' })]

    await openDetail('t1')
    await flushPromises()

    expect(originalCode.value).toBe('')
    expect(toasts.value.some((t) => t.type === 'error')).toBe(false)
  })
})

// ===========================================================================
describe('C2 · 多方竞态（手法：A 延迟最长、且 A 到之前先切走）', () => {
  it('A→B→C 连续切换，A 最后到：C 的内容不被 A/B 覆盖', async () => {
    const d = deferGetExample()
    examples.value = [makeExample({ id: 'A' }), makeExample({ id: 'B' }), makeExample({ id: 'C' })]

    void openDetail('A')
    await flushPromises()
    void openDetail('B')
    await flushPromises()
    void openDetail('C')
    await flushPromises()
    expect(d.calls).toEqual(['A', 'B', 'C'])

    // 逆序回包：最早发的最后到（最恶劣的乱序）
    d.resolve({ id: 'B', code: 'B-code\n' })
    await flushPromises()
    d.resolve({ id: 'A', code: 'A-code\n' })
    await flushPromises()
    d.resolve({ id: 'C', code: 'C-code\n' })
    await flushPromises()

    expect(selectedId.value).toBe('C')
    expect(originalCode.value).toBe('C-code\n')
  })

  it('A→B→A 切回：最终选中的 A 仍能拿到源码（不会被中间态饿死）', async () => {
    const d = deferGetExample()
    examples.value = [makeExample({ id: 'A' }), makeExample({ id: 'B' })]

    void openDetail('A')
    await flushPromises()
    void openDetail('B')
    await flushPromises()
    void openDetail('A')
    await flushPromises()
    expect(d.calls).toEqual(['A', 'B', 'A'])

    d.resolve({ id: 'A', code: 'A-1\n' }) // seq1，已过期
    await flushPromises()
    d.resolve({ id: 'B', code: 'B-code\n' }) // seq2，已过期
    await flushPromises()
    d.resolve({ id: 'A', code: 'A-2\n' }) // seq3，有效
    await flushPromises()

    expect(selectedId.value).toBe('A')
    expect(originalCode.value).toBe('A-2\n')
  })
})

// ===========================================================================
describe('C3 · 同一 id 重复打开（源码不得被自己的序号守卫饿死）', () => {
  it('源码在途时对同一 id 再调一次 openDetail，源码仍应装载完成', async () => {
    const d = deferGetExample()
    examples.value = [makeExample({ id: 'A' })]

    void openDetail('A')
    await flushPromises()
    const first = await openDetail('A') // 第二次：selectedId 已等于 A，走不到装载分支
    await flushPromises()

    d.resolve({ id: 'A', code: 'A-code\n' })
    await flushPromises()

    expect(first).toEqual([])
    // 用户视角：详情页必须显示真实源码，而不是空白
    expect(originalCode.value).toBe('A-code\n')
  })
})

// ===========================================================================
describe('C4 · 保存 / 重试参数 不得顶掉用户内容', () => {
  it('saveExample 末尾重载参数：保留用户刚保存的内容，isDirty 正确复位', async () => {
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 't1', code: 'orig\n' } as never)
    vi.mocked(window.sidecar.saveExample).mockResolvedValue({ json_file: 'a.json' } as never)
    examples.value = [makeExample({ id: 't1' })]

    await openDetail('t1')
    await flushPromises()
    const w = mount(MonacoEditor)
    wrappers.push(w)
    expect(originalCode.value).toBe('orig\n')

    // 用户改成 edited 并标脏
    h.state.value = 'edited\n'
    h.state.listeners[0]()
    await nextTick()
    expect(isDirty.value).toBe(true)

    await saveExample()
    await flushPromises()
    await flushPromises()

    expect(vi.mocked(window.sidecar.saveExample)).toHaveBeenCalledWith('t1', 'edited\n')
    expect(originalCode.value).toBe('edited\n')
    expect(isDirty.value).toBe(false)
    // 编辑器里仍是用户刚保存的内容，没有被重置回旧源码/空串
    expect(h.state.value).toBe('edited\n')
  })

  it('retryParseArgs 时不得把用户未保存的编辑冲掉，也不得错置 isDirty', async () => {
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 't1', code: 'orig\n' } as never)
    examples.value = [makeExample({ id: 't1' })]

    await openDetail('t1')
    await flushPromises()
    const w = mount(MonacoEditor)
    wrappers.push(w)

    h.state.value = 'dirty-edit\n'
    h.state.listeners[0]()
    await nextTick()
    expect(isDirty.value).toBe(true)

    await retryParseArgs()
    await flushPromises()

    expect(originalCode.value).toBe('orig\n') // 基线不得被改写
    expect(h.state.value).toBe('dirty-edit\n') // 用户编辑仍在
    expect(isDirty.value).toBe(true) // 仍是脏的，不能误复位
  })
})

// ===========================================================================
describe('C5 · 运行器：清空与在途响应', () => {
  it('clearRunnerSelection 后 runnerCode 归零，在途响应失效', async () => {
    const d = deferGetExample()
    examples.value = [makeExample({ id: 'r1' })]

    selectRunnerExample('r1')
    await flushPromises()
    expect(runnerSelectedId.value).toBe('r1')

    clearRunnerSelection()
    expect(runnerCode.value).toBe('')
    expect(runnerSelectedId.value).toBe(null)

    d.resolve({ id: 'r1', code: 'late-code\n' })
    await flushPromises()

    expect(runnerCode.value).toBe('') // 清空后到站的响应不得回填
  })

  it('连续选择两个示例，先发的后到时以最后一个为准', async () => {
    const d = deferGetExample()
    examples.value = [makeExample({ id: 'r1' }), makeExample({ id: 'r2' })]

    selectRunnerExample('r1')
    await flushPromises()
    selectRunnerExample('r2')
    await flushPromises()

    d.resolve({ id: 'r1', code: 'r1-code\n' })
    await flushPromises()
    d.resolve({ id: 'r2', code: 'r2-code\n' })
    await flushPromises()

    expect(runnerSelectedId.value).toBe('r2')
    expect(runnerCode.value).toBe('r2-code\n')
  })
})

// ===========================================================================
describe('C6 · 占位串的唯一合法场景', () => {
  it('确实未选中任何示例时，占位串仍然出现（不能因修复而消失）', () => {
    selectedId.value = null
    originalCode.value = ''
    const w = mount(MonacoEditor)
    wrappers.push(w)

    expect(h.create.mock.calls[0][1].value).toBe(PLACEHOLDER)
    expect(vi.mocked(applyMonacoTheme)).toHaveBeenCalledTimes(1)
  })

  it('未选中时编辑器内容变更不得污染 isDirty', async () => {
    selectedId.value = null
    originalCode.value = ''
    const w = mount(MonacoEditor)
    wrappers.push(w)

    h.state.value = 'x'
    h.state.listeners[0]()
    await nextTick()
    expect(isDirty.value).toBe(false)
  })
})

// ===========================================================================
describe('C7 · 未走组件时 store 仍自洽（registerEditor 直连）', () => {
  it('源码装载前编辑器未注册也不抛错', async () => {
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 't1', code: 'code\n' } as never)
    examples.value = [makeExample({ id: 't1' })]

    registerEditor(null)
    await expect(openDetail('t1')).resolves.toEqual([])
    await flushPromises()
    expect(originalCode.value).toBe('code\n')
  })
})

// ===========================================================================
// C8 · openDetail 早退路径的副作用（序号自增位置变更后的回归面）
// 早退路径在 ++_openDetailSeq 之前返回：不得扰动参数区，也不得把 argsLoading 卡在 true
// ===========================================================================
describe('C8 · openDetail 早退路径不得扰动参数区', () => {
  it('示例不存在（!ex 早退）：保留既有参数与 argsLoading，不发起任何请求', async () => {
    currentArgs.value = [{ name: 'x', flags: ['--x'], dest: 'x', type: 'str' }]
    argsLoading.value = false

    const r = await openDetail('nope')

    expect(r).toEqual([])
    expect(currentArgs.value).toHaveLength(1) // 不得被清成 []，否则用户以为"这个示例没有参数"
    expect(argsLoading.value).toBe(false) // 不得卡在 true
    expect(vi.mocked(window.sidecar.parseArgs)).not.toHaveBeenCalled()
    expect(vi.mocked(window.sidecar.getExample)).not.toHaveBeenCalled()
  })

  it('未保存改动守卫（早退）：保留既有参数与 argsLoading，只弹确认', async () => {
    examples.value = [makeExample({ id: 'A' }), makeExample({ id: 'B' })]
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 'A', code: 'A\n' } as never)
    await openDetail('A')
    await flushPromises()
    currentArgs.value = [{ name: 'x', flags: ['--x'], dest: 'x', type: 'str' }]
    isDirty.value = true

    const r = await openDetail('B')

    expect(r).toEqual([])
    expect(confirmPrompt.value).not.toBeNull() // 只弹确认
    expect(selectedId.value).toBe('A') // 不得切换
    expect(currentArgs.value).toHaveLength(1) // 不得被清成 []
    expect(argsLoading.value).toBe(false) // 不得卡在 true
  })

  it('守卫确认后重放：B 正常装载源码与参数，argsLoading 正确回落', async () => {
    examples.value = [makeExample({ id: 'A' }), makeExample({ id: 'B' })]
    vi.mocked(window.sidecar.getExample).mockResolvedValue({ id: 'B', code: 'B-code\n' } as never)
    vi.mocked(window.sidecar.parseArgs).mockResolvedValue({ args: [], count: 0 } as never)
    await openDetail('A')
    await flushPromises()
    isDirty.value = true

    await openDetail('B')
    resolveConfirm(true) // 用户点「放弃修改」
    await flushPromises()

    expect(selectedId.value).toBe('B')
    expect(originalCode.value).toBe('B-code\n')
    expect(vi.mocked(window.sidecar.parseArgs)).toHaveBeenCalledWith('B')
    expect(argsLoading.value).toBe(false) // 关键：不能卡在 true
  })
})

// ===========================================================================
// C9 · 源码在途时用户已在编辑器里打字（缺陷 D1 修复后加固的输入归属）
// 已加 isDirty 守卫：回包落地前若用户敲过字，源码不写入、用户输入保留。
// 本用例是那行守卫的回归护栏——去掉守卫会立刻变红。
// ===========================================================================
describe('C9 · 在途期间用户输入的归属（用户输入优先）', () => {
  it('源码在途时用户敲了字：保留用户输入，服务端源码不落地', async () => {
    const d = deferGetExample()
    examples.value = [makeExample({ id: 't1' })]

    void openDetail('t1')
    await flushPromises()
    // 编辑器已挂载（单例、打开即可输入），用户在空编辑器里敲了字
    const w = mount(MonacoEditor)
    wrappers.push(w)
    h.state.value = 'user-typed'
    onEditorContentChanged('user-typed')
    expect(isDirty.value).toBe(true)

    d.resolve({ id: 't1', code: 'server\n' })
    await flushPromises()

    // 用户输入胜出：源码不落地（基线仍是空），脏标记保留
    expect(originalCode.value).toBe('')
    expect(isDirty.value).toBe(true)
    // 用户敲的内容仍留在编辑器里，没有被 setValue 覆盖
    expect(h.state.value).toBe('user-typed')
  })
})
