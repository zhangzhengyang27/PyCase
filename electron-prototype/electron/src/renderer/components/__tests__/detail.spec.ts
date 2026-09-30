// 详情链路组件测试：DetailPage / RunnerView / CommandPalette / MonacoEditor。
// 与 base.spec.ts 的分工：这一层全部直接读写 store 域的模块级单例，因此每个用例
// 前后都要归零被触碰的响应式状态；否则上一个用例的 selectedId / 输出汇会串味。
import { describe, expect, it, afterEach, beforeEach, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'

import DetailPage from '../DetailPage.vue'
import RunnerView from '../RunnerView.vue'
import CommandPalette from '../CommandPalette.vue'
import MonacoEditor from '../MonacoEditor.vue'
import { assets } from '../../src/store/assets'
import { examples, type VExample } from '../../src/store/catalog'
import { currentArgs, currentRunId, isDirty, isRunning, originalCode, runStatusText, saveExample, saving, selectedId, surfaceState } from '../../src/store/detail'
import { getTestApi } from '../../src/store/index'
import { runTimeout, favorites, runHistory } from '../../src/store/prefs'
import { runnerArgsLine, runnerQuery, runnerSelectedId } from '../../src/store/runner'
import type { RunHistoryEntry } from '../../src/types'
import { toasts } from '../../toast'
import { applyMonacoTheme } from '../../monaco'

// ---------------------------------------------------------------------------
// Monaco 桩
// ---------------------------------------------------------------------------
// src/renderer/monaco.ts 在模块求值时 import 了 `?worker` 资源并 defineTheme，
// 两者在 Vitest 下都无法求值；而 MonacoEditor.vue 与 DetailPage.vue 都间接 import 它，
// 因此必须在文件顶层替换掉整个模块。
//
// 假编辑器做成有状态的：create 时用 options.value 初始化，setValue 改写它，
// getValue 读回——这样「注册进 store 的编辑器」与「组件持有的编辑器」是同一份内容，
// saveExample / isDirty 这类依赖取值的断言才有意义。
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

// restoreMocks 会重置 mock 实现，故每个用例开头重新装一遍桩行为（比依赖默认实现稳）。
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

// ---------------------------------------------------------------------------
// 夹具与工具
// ---------------------------------------------------------------------------
function makeExample(over: Partial<VExample> = {}): VExample {
  return {
    id: 't1',
    name: 'alpha.py',
    category: 'topics',
    path: 'topics/alpha.py',
    code: 'print(1)\n',
    title: 'Alpha',
    tags: [],
    quality_score: 90,
    run_status: 'runnable',
    _tagsAll: [],
    ...over
  }
}

function makeRun(id: string, i = 0): RunHistoryEntry {
  return {
    ts: `2026-01-0${(i % 9) + 1}T08:00:00.000Z`,
    id,
    name: `${id}.py`,
    args: [],
    duration_ms: 12,
    exit_code: 0,
    ok: true
  }
}

// 组件不 unmount 会把 window keydown 监听留在全局，跨用例互相触发 saveExample/运行。
// 统一登记、统一拆除，比每个用例手动 unmount 更不容易漏。
const wrappers: VueWrapper[] = []

function track(w: VueWrapper): VueWrapper {
  wrappers.push(w)
  return w
}

function unmountNow(w: VueWrapper): void {
  const i = wrappers.indexOf(w)
  if (i >= 0) wrappers.splice(i, 1)
  w.unmount()
}

function buttonByText(w: VueWrapper, text: string) {
  const found = w.findAll('button').find((b) => b.text().includes(text))
  if (!found) throw new Error(`未找到按钮: ${text}`)
  return found
}

// getTestApi 的声明返回 Record<string, unknown>，调用其方法需要显式收窄。
const testApi = getTestApi() as unknown as { resetViewFilters: () => void }

function resetStore(): void {
  examples.value = []
  selectedId.value = null
  originalCode.value = ''
  isDirty.value = false
  saving.value = false
  currentArgs.value = []
  assets.value = []
  isRunning.value = false
  runStatusText.value = '就绪'
  runTimeout.value = 30
  runHistory.value = []
  favorites.value = new Set()
  runnerSelectedId.value = null
  runnerQuery.value = ''
  runnerArgsLine.value = ''
  for (const key of ['detail', 'runner'] as const) {
    const st = surfaceState(key)
    st.lines = []
    st.images = []
    st.dot = 'idle'
    st.truncated = false
  }
  testApi.resetViewFilters()
}

beforeEach(() => {
  resetStore()
  resetMonaco()
  // jsdom 未实现 scrollIntoView；CommandPalette 在高亮项变化后会调用它。
  Element.prototype.scrollIntoView = () => {}
})

afterEach(() => {
  for (const w of wrappers.splice(0)) w.unmount()
  document.body.innerHTML = ''
  toasts.value = []
})

// ===========================================================================
// DetailPage
// ===========================================================================
describe('DetailPage', () => {
  function mountDetail(over: Partial<VExample> = {}): VueWrapper {
    const ex = makeExample(over)
    examples.value = [ex]
    selectedId.value = ex.id
    originalCode.value = ex.code || ''
    return track(mount(DetailPage, { attachTo: document.body }))
  }

  it('缺依赖时给出「安装依赖」入口：点击后装依赖并按结果重跑（A6 失败恢复）', async () => {
    vi.mocked(window.sidecar.installExampleDeps).mockResolvedValue({
      installed: ['requests'],
      failed: [],
      packages: ['requests']
    })
    const w = mountDetail({ run_status: 'missing_deps' })
    const btn = w.get('[data-testid="install-deps"]')
    expect(btn.text()).toContain('安装依赖')

    await btn.trigger('click')
    await flushPromises()

    expect(window.sidecar.installExampleDeps).toHaveBeenCalledWith('t1')
    // 装完即重跑（用户点这个按钮的意图）
    expect(window.sidecar.runExample).toHaveBeenCalled()
    expect(toasts.value.some((t) => t.text.includes('已安装 1 个依赖'))).toBe(true)
  })

  it('运行输出出现 ImportError 时同样给出安装入口（清单漏声明的漏网场景）', async () => {
    const w = mountDetail({ run_status: 'runnable' })
    expect(w.find('[data-testid="install-deps"]').exists()).toBe(false)

    surfaceState('detail').lines.push({ text: "ModuleNotFoundError: No module named 'requests'", cls: 'base' })
    await nextTick()
    expect(w.find('[data-testid="install-deps"]').exists()).toBe(true)
  })

  it('版本页：列出编辑历史、预览显示行级差异、可还原（A6 可恢复编辑）', async () => {
    vi.mocked(window.sidecar.listVersions).mockResolvedValue({
      id: 't1',
      versions: [{ ts: '20260929-231500-ab12cd34', bytes: 1024, sha256: 'x' }]
    })
    vi.mocked(window.sidecar.readVersion).mockResolvedValue({
      id: 't1',
      ts: '20260929-231500-ab12cd34',
      code: 'print(1)\nprint(2)\n'
    })
    vi.mocked(window.sidecar.restoreVersion).mockResolvedValue({ id: 't1', restored: '20260929-231500-ab12cd34' })
    vi.mocked(window.sidecar.getExample).mockResolvedValue({
      id: 't1',
      name: 'alpha.py',
      code: 'print(1)\n',
      title: 'Alpha',
      category: 'topics',
      tags: [],
      path: '/tmp/alpha.py'
    } as never)

    const w = mountDetail({ code: 'print(1)\n' })
    const tabs = Array.from(w.findAll('[role="tab"]'))
    const versionTab = tabs.find((t) => t.text() === '版本')!
    await versionTab.trigger('click')
    await flushPromises()

    expect(window.sidecar.listVersions).toHaveBeenCalledWith('t1')
    const panel = w.get('[data-testid="versions-panel"]')
    expect(panel.text()).toContain('2026-09-29 23:15:00')

    // 预览：与当前编辑器内容（print(1)）比较 → 一行 too many
    await panel.get('[data-testid="version-20260929-231500-ab12cd34"]').trigger('click')
    await flushPromises()
    const diff = w.get('[data-testid="version-diff"]')
    expect(diff.text()).toContain('+print(2)')
    expect(diff.text()).toContain('还原后将')

    // 还原：调 sidecar 并同步编辑器基线（不显示成"有未保存修改"）
    await diff.get('[data-testid="version-restore"]').trigger('click')
    await flushPromises()
    expect(window.sidecar.restoreVersion).toHaveBeenCalledWith('t1', '20260929-231500-ab12cd34')
    expect(isDirty.value).toBe(false)
    expect(window.sidecar.getExample).toHaveBeenCalledWith('t1')
  })

  it('未选中示例时不渲染详情区，选中后渲染头部标题与分类', () => {
    const empty = track(mount(DetailPage, { attachTo: document.body }))
    expect(empty.find('section').exists()).toBe(false)

    const w = mountDetail({ title: 'Alpha', category: 'topics' })
    expect(w.find('section').exists()).toBe(true)
    expect(w.get('span[title="Alpha"]').text()).toBe('Alpha')
    expect(w.text()).toContain('topics')
  })

  it('无 title 时回退文件名（去扩展名、下划线转空格），dirty 时标题追加 ●', async () => {
    const w = mountDetail({ title: undefined, name: 'hello_world.py' })
    expect(w.get('span[title="hello world"]').text()).toBe('hello world')

    isDirty.value = true
    await nextTick()
    expect(w.get('span[title="hello world ●"]').text()).toBe('hello world ●')
  })

  it('路径副标题为「分类 / id」，无 id 时回退文件名', () => {
    const withId = mountDetail({ id: 't1', category: 'topics' })
    expect(withId.find('span[title="topics / t1"]').exists()).toBe(true)

    const noId = mountDetail({ id: '', name: 'x.py', category: 'tools' })
    expect(noId.find('span[title="tools / x.py"]').exists()).toBe(true)
  })

  it('质量分按档取文字色，缺省显示 0', () => {
    const high = mountDetail({ quality_score: 90 })
    const highBadge = high.get('[title="六维质量评分（0-100）"]')
    expect(highBadge.text()).toContain('90')
    expect(highBadge.classes()).toContain('text-ink-mute')

    const mid = mountDetail({ quality_score: 60 })
    expect(mid.get('[title="六维质量评分（0-100）"]').classes()).toContain('text-ink-mute')

    const none = mountDetail({ quality_score: undefined })
    const noneBadge = none.get('[title="六维质量评分（0-100）"]')
    expect(noneBadge.text()).toContain('0')
    expect(noneBadge.classes()).toContain('text-warn')
  })

  it('运行状态徽章只对已知状态渲染，未知状态整段省略', () => {
    const broken = mountDetail({ run_status: 'broken' })
    expect(broken.text()).toContain('语法损坏')
    const brokenEl = broken.get('[title="代码存在语法错误，无法运行"]')
    expect(brokenEl.classes()).toContain('text-ink-mute')
    expect(brokenEl.find('.stat-dot').classes()).toContain('bg-ink-faint')

    const missing = mountDetail({ run_status: 'missing_deps' })
    expect(missing.text()).toContain('缺依赖')
    const missingEl = missing.get('[title="依赖的第三方库在共享运行环境中缺失，运行会因 ImportError 失败"]')
    expect(missingEl.find('.stat-dot').classes()).toContain('bg-warn')

    const unknown = mountDetail({ run_status: undefined })
    expect(unknown.text()).not.toContain('语法损坏')
    expect(unknown.text()).not.toContain('缺依赖')
  })

  it('可运行性徽章与卡片同口径：runnable 不渲染，risky 交给高危徽章', () => {
    // runnable 是正向状态，卡片刻意不展示（见 utils.ts 中 RUN_STATUS_LABELS 上方注释），
    // 详情页同样不该多出一个卡片刻意不显示的「可运行」徽章
    const runnable = mountDetail({ run_status: 'runnable' })
    expect(runnable.find('[title*="静态检查通过"]').exists()).toBe(false)
    expect(runnable.text()).not.toContain('可运行')

    // risky：run_status 徽章整段省略，只保留 risk_high 的高危徽章，避免两个「高危」并存
    const risky = mountDetail({ run_status: 'risky', risk_high: true })
    expect(risky.find('[title*="子进程隔离不是安全沙箱"]').exists()).toBe(false)
    expect(risky.findAll('[title="含高危操作（系统命令/文件删除等），运行前请先审阅代码"]')).toHaveLength(1)
  })

  it('risk_high 时渲染高危徽章，普通示例不渲染', () => {
    expect(mountDetail({ risk_high: true }).text()).toContain('高危')
    expect(mountDetail({ risk_high: false }).text()).not.toContain('高危')
  })

  it('标签最多展示 3 个并折叠为 +N', () => {
    const few = mountDetail({ tags: ['a', 'b'] })
    expect(few.findAll('span.bg-card')).toHaveLength(2)
    expect(few.text()).not.toContain('+2')

    const many = mountDetail({ tags: ['a', 'b', 'c', 'd', 'e'] })
    expect(many.findAll('span.bg-card')).toHaveLength(3)
    expect(many.text()).toContain('+2')
  })

  it('头部图标 chip 出 Lucide 图标（v2 无 emoji/色相）', () => {
    const hit = mountDetail({ tags: ['基础'] })
    const chipHit = hit.findAll('.chip-ic')[0]
    expect(chipHit.find('svg').exists()).toBe(true)
    expect(chipHit.text()).toBe('')

    const miss = mountDetail({ tags: [] })
    expect(miss.findAll('.chip-ic')[0].find('svg').exists()).toBe(true)
  })

  it('收藏按钮文案随 store 状态切换，点击后写入/移出收藏集合', async () => {
    const w = mountDetail({ id: 't1' })
    expect(w.find('button[aria-label="收藏"]').exists()).toBe(true)

    await w.get('button[aria-label="收藏"]').trigger('click')
    expect(favorites.value.has('t1')).toBe(true)
    expect(w.find('button[aria-label="取消收藏"]').exists()).toBe(true)

    await w.get('button[aria-label="取消收藏"]').trigger('click')
    expect(favorites.value.has('t1')).toBe(false)
    expect(w.find('button[aria-label="收藏"]').exists()).toBe(true)
  })

  it('删除按钮仅用户集合示例可见；确认后调用 deleteExample 并关闭详情', async () => {
    const builtin = mountDetail({ id: 't1', user_collection: false })
    expect(builtin.find('button[aria-label="删除此示例"]').exists()).toBe(false)

    const user = mountDetail({ id: 'u1', user_collection: true, collection: '我的集合' })
    await user.get('button[aria-label="删除此示例"]').trigger('click')
    await nextTick()

    const dialog = document.body.querySelector('[role="dialog"]')!
    expect(dialog.textContent).toContain('删除示例')
    expect(dialog.textContent).toContain('我的集合')

    const delBtn = Array.from(dialog.querySelectorAll('button')).find((b) => b.textContent?.trim() === '删除')!
    delBtn.click()
    await flushPromises()

    expect(vi.mocked(window.sidecar.deleteExample)).toHaveBeenCalledWith('u1')
    // deleteUserExample 成功后置空 selectedId 并重载列表 → 详情区消失
    expect(user.find('section').exists()).toBe(false)
  })

  it('保存按钮在非 dirty 或保存中禁用，文案随之切换', async () => {
    const w = mountDetail()
    expect(buttonByText(w, '保存').attributes('disabled')).toBeDefined()

    isDirty.value = true
    await nextTick()
    expect(buttonByText(w, '保存').attributes('disabled')).toBeUndefined()

    saving.value = true
    await nextTick()
    expect(buttonByText(w, '保存').attributes('disabled')).toBeDefined()
    expect(buttonByText(w, '保存中…').text()).toContain('保存中…')
  })

  it('运行按钮把 runTimeout 传给 sidecar；运行中换成停止按钮并调用 stopRun', async () => {
    const w = mountDetail({ id: 't1' })
    runTimeout.value = 42

    expect(buttonByText(w, '运行').attributes('title')).toBe('运行 (Cmd+Enter)')
    await buttonByText(w, '运行').trigger('click')
    await flushPromises()
    expect(vi.mocked(window.sidecar.runExample)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(window.sidecar.runExample).mock.calls[0][0]).toMatchObject({ id: 't1', timeout: 42 })

    isRunning.value = true
    currentRunId.value = 'r1'
    await nextTick()
    expect(w.find('button[title="运行 (Cmd+Enter)"]').exists()).toBe(false)
    const stop = w.get('button[title="停止 (Cmd+.)"]')
    await stop.trigger('click')
    await flushPromises()
    expect(vi.mocked(window.sidecar.stopRun)).toHaveBeenCalledWith('r1')
  })

  it('Cmd+S 保存、Cmd+Enter 运行、Cmd+. 停止；无修饰键时全部不触发', async () => {
    const w = mountDetail({ id: 't1' })
    isDirty.value = true
    await nextTick()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 's' }))
    await flushPromises()
    expect(vi.mocked(window.sidecar.saveExample)).not.toHaveBeenCalled()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', metaKey: true }))
    await flushPromises()
    expect(vi.mocked(window.sidecar.saveExample)).toHaveBeenCalledWith('t1', 'print(1)\n')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', metaKey: true }))
    await flushPromises()
    expect(vi.mocked(window.sidecar.runExample)).toHaveBeenCalledTimes(1)

    isRunning.value = true
    currentRunId.value = 'r1'
    await nextTick()
    expect(w.find('button[title="停止 (Cmd+.)"]').exists()).toBe(true)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: '.', metaKey: true }))
    await flushPromises()
    expect(vi.mocked(window.sidecar.stopRun)).toHaveBeenCalledWith('r1')
  })

  it('返回按钮调用 closeDetail；有未保存修改时受 confirm 守卫', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const w = mountDetail({ id: 't1' })
    isDirty.value = true
    await nextTick()

    await w.get('button[aria-label="返回画廊"]').trigger('click')
    expect(confirmSpy).toHaveBeenCalled()
    expect(selectedId.value).toBe('t1')

    confirmSpy.mockReturnValue(true)
    await w.get('button[aria-label="返回画廊"]').trigger('click')
    await nextTick()
    expect(selectedId.value).toBe(null)
    expect(w.find('section').exists()).toBe(false)
  })

  it('参数面板：无参数整区隐藏，有参数显示计数并可折叠；必填缺失给出提示', async () => {
    const w = mountDetail()
    expect(w.find('button[aria-expanded]').exists()).toBe(false)

    currentArgs.value = [
      { name: 'width', flags: ['--width'], dest: 'width', type: 'int' },
      { name: 'out', flags: ['--out'], dest: 'out', type: 'str', required: true }
    ]
    await nextTick()

    const toggle = w.get('button[aria-expanded]')
    expect(toggle.text()).toContain('命令行参数')
    expect(toggle.text()).toContain('(2)')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(w.text()).toContain('存在必填参数，请填写后再运行')

    await toggle.trigger('click')
    expect(w.get('button[aria-expanded]').attributes('aria-expanded')).toBe('false')
    // 折叠只是 v-show，表单节点仍在 DOM 里
    expect(w.find('.flex-wrap').attributes('style') ?? '').toContain('display: none')
  })

  it('三标签切换驱动 v-show 面板与 aria-selected，资源数徽章跟随 assets', async () => {
    assets.value = [{ filename: 'a.png', size: 2048, modified: 0, is_image: true }]
    const w = mountDetail()

    expect(w.get('#detail-tab-output').attributes('aria-selected')).toBe('true')
    expect(w.get('#detail-tab-assets').text()).toContain('(1)')

    await w.get('#detail-tab-history').trigger('click')
    expect(w.get('#detail-tab-history').attributes('aria-selected')).toBe('true')
    expect(w.get('#detail-tab-output').attributes('aria-selected')).toBe('false')
    expect(w.get('#detail-panel-output').attributes('style') ?? '').toContain('display: none')
    expect(w.get('#detail-panel-history').attributes('style') ?? '').not.toContain('display: none')
    // v2：标签页走 .tab 组件类，选中态由 CSS 按平台（mac 抬起段 / win 下划线）表达，
    // 断言只认语义属性 aria-selected（上面已断言），不再耦合具体样式类
    expect(w.get('#detail-tab-history').classes()).toContain('tab')
    expect(w.find('.tab-row').exists()).toBe(true)
  })

  it('清空按钮清空 detail 输出汇；状态点跟随 surfaceState', async () => {
    const st = surfaceState('detail')
    st.lines.push({ text: 'hello', cls: 'base' })
    st.dot = 'success'
    runStatusText.value = '运行成功'
    const w = mountDetail()

    expect(w.get('span[title="运行成功"]').classes()).toContain('bg-ok')

    await buttonByText(w, '清空').trigger('click')
    expect(st.lines).toHaveLength(0)
    expect(st.dot).toBe('idle')
    expect(w.get('span[title="就绪"]').classes()).toContain('bg-ink-faint')

    st.dot = 'error'
    runStatusText.value = '运行失败'
    await nextTick()
    expect(w.get('span[title="运行失败"]').classes()).toContain('bg-danger')
  })
})

// ===========================================================================
// RunnerView
// ===========================================================================
describe('RunnerView', () => {
  function mountRunner(): VueWrapper {
    return track(mount(RunnerView))
  }

  function searchInput(w: VueWrapper) {
    return w.get('input[aria-label="快速查找示例"]')
  }

  it('未选择示例时源码区显示引导文案，选择后显示文件名与只读代码', async () => {
    const w = mountRunner()
    expect(w.get('pre').text()).toContain('在上方搜索并选择示例')
    expect(w.text()).not.toContain('alpha.py')

    examples.value = [makeExample({ id: 't1', name: 'alpha.py', code: 'print(1)\n' })]
    runnerSelectedId.value = 't1'
    await nextTick()

    expect(w.get('pre').text()).toContain('print(1)')
    expect(w.text()).toContain('alpha.py')
    expect(w.text()).not.toContain('在上方搜索并选择示例')
  })

  it('搜索按名称匹配（大小写不敏感）并截断到 8 条', async () => {
    examples.value = Array.from({ length: 10 }, (_, i) => makeExample({ id: `h${i}`, name: `hit_${i}.py` }))
    const w = mountRunner()
    await searchInput(w).setValue('HIT')

    const hits = w.findAll('button[data-active]')
    expect(hits).toHaveLength(8)
    expect(hits[0].text()).toContain('hit_0.py')
  })

  it('仅按名称匹配（标题不参与），无匹配显示提示，Esc 清空搜索', async () => {
    examples.value = [makeExample({ id: 't1', name: 'x.py', title: 'alpha' })]
    const w = mountRunner()
    await searchInput(w).setValue('alpha')

    expect(w.text()).toContain('无匹配示例')
    expect(w.findAll('button[data-active]')).toHaveLength(0)

    await searchInput(w).trigger('keydown', { key: 'Escape' })
    expect(runnerQuery.value).toBe('')
    expect(w.text()).not.toContain('无匹配示例')
  })

  it('↑↓ 在命中列表内回绕，Enter 选中高亮项，查询变化重置高亮', async () => {
    examples.value = ['a', 'b', 'c'].map((n) => makeExample({ id: n, name: `${n}.py` }))
    const w = mountRunner()
    await searchInput(w).setValue('.py')

    const hits = () => w.findAll('button[data-active]')
    expect(hits()).toHaveLength(3)
    expect(hits()[0].attributes('data-active')).toBe('true')

    await searchInput(w).trigger('keydown', { key: 'ArrowDown' })
    expect(hits()[1].attributes('data-active')).toBe('true')

    // 从 0 再往上回绕到最后一条
    await searchInput(w).trigger('keydown', { key: 'ArrowUp' })
    await searchInput(w).trigger('keydown', { key: 'ArrowUp' })
    expect(hits()[2].attributes('data-active')).toBe('true')

    await searchInput(w).trigger('keydown', { key: 'Enter' })
    expect(runnerSelectedId.value).toBe('c')

    // 选中会清空搜索；重新输入后高亮回到第一条
    await searchInput(w).setValue('a.py')
    expect(hits()).toHaveLength(1)
    expect(hits()[0].attributes('data-active')).toBe('true')
  })

  it('点击命中项选中示例并清空搜索框', async () => {
    examples.value = [makeExample({ id: 't1', name: 'alpha.py', code: 'print(1)\n' })]
    const w = mountRunner()
    await searchInput(w).setValue('alpha')
    await w.get('button[data-active]').trigger('click')

    expect(runnerSelectedId.value).toBe('t1')
    expect(runnerQuery.value).toBe('')
    expect(w.get('pre').text()).toContain('print(1)')
  })

  it('未选择时运行按钮禁用；选择后按 splitArgs 解析的单行参数运行', async () => {
    const w = mountRunner()
    const runBtn = () => w.get('button[title="运行 (Cmd+Enter)"]')
    expect(runBtn().attributes('disabled')).toBeDefined()

    examples.value = [makeExample({ id: 't1', name: 'alpha.py' })]
    runnerSelectedId.value = 't1'
    await nextTick()
    expect(runBtn().attributes('disabled')).toBeUndefined()

    await w.get('input[aria-label="命令行参数"]').setValue('--width 100 --name "a b"')
    await runBtn().trigger('click')
    await flushPromises()

    expect(vi.mocked(window.sidecar.runExample)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(window.sidecar.runExample).mock.calls[0][0]).toMatchObject({
      id: 't1',
      args: ['--width', '100', '--name', 'a b']
    })
  })

  it('参数框回车直接运行', async () => {
    examples.value = [makeExample({ id: 't1' })]
    runnerSelectedId.value = 't1'
    runnerArgsLine.value = '--x 1'
    const w = mountRunner()

    await w.get('input[aria-label="命令行参数"]').trigger('keydown.enter')
    await flushPromises()
    expect(vi.mocked(window.sidecar.runExample)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(window.sidecar.runExample).mock.calls[0][0]).toMatchObject({ args: ['--x', '1'] })
  })

  it('运行中显示停止按钮并调用 stopRun；状态点四态配色', async () => {
    examples.value = [makeExample({ id: 't1' })]
    const w = mountRunner()
    const dot = () => w.get('span.w-2.h-2.rounded-full')
    expect(dot().classes()).toContain('bg-ink-faint')

    isRunning.value = true
    currentRunId.value = 'r1'
    await nextTick()
    expect(dot().classes()).toContain('bg-warn')
    expect(dot().classes()).toContain('animate-pulse')
    expect(w.find('button[title="运行 (Cmd+Enter)"]').exists()).toBe(false)

    await w.get('button[title="停止 (Cmd+.)"]').trigger('click')
    await flushPromises()
    expect(vi.mocked(window.sidecar.stopRun)).toHaveBeenCalledWith('r1')

    isRunning.value = false
    runStatusText.value = '运行成功'
    await nextTick()
    expect(dot().classes()).toContain('bg-ok')

    runStatusText.value = '运行失败'
    await nextTick()
    expect(dot().classes()).toContain('bg-danger')
  })

  it('清空按钮清空 runner 输出汇', async () => {
    const st = surfaceState('runner')
    st.lines.push({ text: 'x', cls: 'base' })
    const w = mountRunner()

    await buttonByText(w, '清空').trigger('click')
    expect(st.lines).toHaveLength(0)
    expect(st.dot).toBe('idle')
  })
})

// ===========================================================================
// CommandPalette（Teleport 到 body，查询一律走 document.body）
// ===========================================================================
describe('CommandPalette', () => {
  function mountPalette(): VueWrapper {
    return track(mount(CommandPalette, { attachTo: document.body }))
  }

  function setQuery(text: string): void {
    const input = document.body.querySelector<HTMLInputElement>('input[aria-label="全局搜索示例"]')!
    input.value = text
    input.dispatchEvent(new Event('input', { bubbles: true }))
  }

  function matchItems(): NodeListOf<HTMLElement> {
    return document.body.querySelectorAll<HTMLElement>('button[data-active]')
  }

  /**
   * 真实浏览器路径：面板打开后搜索框已聚焦，按键事件的 target 是 input。
   * 必须按这个路径派发——直接派发到 window 会绕过「input 上的监听器」这一环，
   * 从而掩盖「同一个按键被处理两次」的缺陷（曾据此漏掉 ↑↓ 一次跨两行）。
   */
  function pressKey(key: string): void {
    const input = document.body.querySelector<HTMLInputElement>('input[aria-label="全局搜索示例"]')!
    input.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }))
  }

  function activeIndexOf(): number {
    return Array.from(matchItems()).findIndex((e) => e.getAttribute('data-active') === 'true')
  }

  it('挂载后渲染到 body 并聚焦搜索框', () => {
    mountPalette()
    const input = document.body.querySelector('input[aria-label="全局搜索示例"]')
    expect(input).toBeTruthy()
    expect(document.activeElement).toBe(input)
  })

  it('空查询渲染示例分组并截断到 12 条', () => {
    examples.value = Array.from({ length: 15 }, (_, i) => makeExample({ id: `e${i}`, name: `ex_${i}.py` }))
    mountPalette()

    const items = matchItems()
    expect(items).toHaveLength(12)
    expect(items[0].textContent).toContain('ex_0.py')
    expect(document.body.textContent).toContain('示例')
  })

  it('最近运行按 id 去重取前 5', () => {
    examples.value = ['a', 'b', 'c', 'd', 'e'].map((n) => makeExample({ id: n, name: `${n}.py` }))
    runHistory.value = ['a', 'a', 'b', 'c', 'd', 'e'].map((id, i) => makeRun(id, i))
    mountPalette()

    const rows = document.body.querySelectorAll('div[role="button"]')
    expect(rows).toHaveLength(5)
    expect(rows[0].textContent).toContain('a.py')
    expect(document.body.textContent).toContain('最近运行')
  })

  it('查询命中名称或标签，并排除已在最近项中的示例', async () => {
    examples.value = [
      makeExample({ id: 'apple', name: 'apple.py', title: undefined }),
      makeExample({ id: 'banana', name: 'banana.py', title: undefined }),
      makeExample({ id: 'cherry', name: 'cherry.py', title: undefined, _tagsAll: ['爬虫'] })
    ]
    runHistory.value = [makeRun('apple')]
    mountPalette()

    setQuery('a')
    await nextTick()
    // apple 被最近项占用而排除；cherry 名称/标签都不含 a
    expect(matchItems()).toHaveLength(1)
    expect(matchItems()[0].textContent).toContain('banana.py')
    // 非空查询下最近分组整体隐藏
    expect(document.body.textContent).not.toContain('最近运行')

    setQuery('爬虫')
    await nextTick()
    expect(matchItems()).toHaveLength(1)
    expect(matchItems()[0].textContent).toContain('cherry.py')
  })

  it('空库与无匹配分别给出不同空态文案', async () => {
    mountPalette()
    expect(document.body.textContent).toContain('库中暂无示例')

    examples.value = [makeExample({ id: 't1', name: 'alpha.py', title: undefined })]
    setQuery('zzz')
    await nextTick()
    expect(document.body.textContent).toContain('没有匹配的示例')
  })

  it('↑↓ 在平铺列表内回绕，Enter 打开高亮项并关闭面板', async () => {
    examples.value = ['a', 'b', 'c'].map((n) => makeExample({ id: n, name: `${n}.py`, title: undefined }))
    const w = mountPalette()
    setQuery('py')
    await nextTick()
    expect(matchItems()).toHaveLength(3)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await nextTick()
    expect(activeIndexOf()).toBe(1)

    // 从 0 再往上回绕到最后一条
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }))
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }))
    await nextTick()
    expect(activeIndexOf()).toBe(2)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    await nextTick()
    expect(selectedId.value).toBe('c')
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('搜索框聚焦时，单次 ↑↓ 只移动一行（回归：曾因双重监听一次跨两行）', async () => {
    examples.value = ['a', 'b', 'c'].map((n) => makeExample({ id: n, name: `${n}.py`, title: undefined }))
    mountPalette()
    setQuery('py')
    await nextTick()
    expect(activeIndexOf()).toBe(0)

    pressKey('ArrowDown')
    await nextTick()
    expect(activeIndexOf()).toBe(1)
  })

  it('搜索框聚焦时，单次 Enter 只打开一次并只 emit 一次 close（回归：曾触发两次）', async () => {
    examples.value = [makeExample({ id: 't1', name: 'alpha.py', title: undefined })]
    const w = mountPalette()
    setQuery('alpha')
    await nextTick()

    pressKey('Enter')
    await nextTick()
    expect(selectedId.value).toBe('t1')
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('Escape 关闭面板', async () => {
    const w = mountPalette()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('点击遮罩自身关闭面板', async () => {
    const w = mountPalette()
    const mask = document.body.querySelector('.scrim') as HTMLElement
    mask.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await nextTick()
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('点击条目打开详情并关闭面板', async () => {
    examples.value = [makeExample({ id: 't1', name: 'alpha.py', title: undefined })]
    const w = mountPalette()
    setQuery('alpha')
    await nextTick()

    matchItems()[0].click()
    await nextTick()
    expect(selectedId.value).toBe('t1')
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('最近项的「运行」按钮直接运行，且不冒泡成第二次打开', async () => {
    examples.value = [makeExample({ id: 't1', name: 'alpha.py' })]
    runHistory.value = [makeRun('t1')]
    const w = mountPalette()

    const runBtn = document.body.querySelector('button[aria-label="直接运行"]') as HTMLElement
    runBtn.click()
    await flushPromises()

    expect(vi.mocked(window.sidecar.runExample)).toHaveBeenCalledTimes(1)
    // @click.stop 生效：只 emit 一次 close（否则行本身的 openItem 也会再发一次）
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('Cmd+Enter 直接运行高亮项', async () => {
    examples.value = [makeExample({ id: 't1', name: 'alpha.py', title: undefined })]
    mountPalette()
    setQuery('alpha')
    await nextTick()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', metaKey: true }))
    await flushPromises()
    expect(vi.mocked(window.sidecar.runExample)).toHaveBeenCalledTimes(1)
  })

  it('卸载时移除同一个 window keydown 监听，避免跨用例泄漏', () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    const removeSpy = vi.spyOn(window, 'removeEventListener')
    const w = mountPalette()

    const handler = addSpy.mock.calls.find((c) => c[0] === 'keydown')?.[1]
    expect(typeof handler).toBe('function')

    unmountNow(w)
    expect(removeSpy.mock.calls.some((c) => c[0] === 'keydown' && c[1] === handler)).toBe(true)
  })
})

// ===========================================================================
// MonacoEditor（../../monaco 已被替换为上面的桩）
// ===========================================================================
describe('MonacoEditor', () => {
  function mountEditor(): VueWrapper {
    return track(mount(MonacoEditor))
  }

  it('挂载时以 originalCode 创建编辑器、应用主题并注册进 store', async () => {
    originalCode.value = 'print(1)\n'
    selectedId.value = 't1'
    mountEditor()

    expect(vi.mocked(applyMonacoTheme)).toHaveBeenCalledTimes(1)
    expect(h.create).toHaveBeenCalledTimes(1)
    const opts = h.create.mock.calls[0][1]
    expect(opts.value).toBe('print(1)\n')
    expect(opts.language).toBe('python')
    expect(opts.theme).toBe('pycase-dark')
    expect(opts.readOnly).toBe(false)

    // 注册生效的证明：saveExample 经注册的 getValue 取到编辑器当前内容
    isDirty.value = true
    await saveExample()
    expect(vi.mocked(window.sidecar.saveExample)).toHaveBeenCalledWith('t1', 'print(1)\n')
  })

  it('originalCode 为空时以占位代码创建', () => {
    originalCode.value = ''
    mountEditor()
    expect(h.create.mock.calls[0][1].value).toBe('# 在画廊或工具箱中选择示例查看与编辑代码\n')
  })

  it('originalCode 变化时经 setValue 同步，内容已相同时不重复写入', async () => {
    originalCode.value = 'a'
    mountEditor()

    originalCode.value = 'b'
    await nextTick()
    expect(h.fakeEditor.setValue).toHaveBeenCalledWith('b')

    h.fakeEditor.setValue.mockClear()
    // 模拟编辑器内容已被用户改成 c（不经过 watch），再把 originalCode 对齐到同一值
    h.state.value = 'c'
    originalCode.value = 'c'
    await nextTick()
    expect(h.fakeEditor.setValue).not.toHaveBeenCalled()
  })

  it('内容变更回调仅在已选中示例时判定 isDirty', async () => {
    originalCode.value = 'a'
    selectedId.value = 't1'
    mountEditor()
    const onChange = h.state.listeners[0]
    expect(typeof onChange).toBe('function')

    h.state.value = 'b'
    onChange()
    await nextTick()
    expect(isDirty.value).toBe(true)

    // 未选中示例时编辑内容不应污染 dirty 标记
    isDirty.value = false
    selectedId.value = null
    h.state.value = 'c'
    onChange()
    await nextTick()
    expect(isDirty.value).toBe(false)
  })

  it('卸载时销毁编辑器实例', () => {
    originalCode.value = 'a'
    const w = mountEditor()
    unmountNow(w)
    expect(h.fakeEditor.dispose).toHaveBeenCalledTimes(1)
  })
})
