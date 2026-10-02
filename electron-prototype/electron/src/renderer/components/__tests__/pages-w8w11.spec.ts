// W8-W11 框架件：sidecar 输出解析 / quickRun 自动运行 / 向导步骤 / sidecar 结果渲染。
import { beforeEach, describe, expect, it, vi } from 'vitest'

const hoisted = vi.hoisted(() => ({
  runSnippet: vi.fn()
}))

vi.mock('../../src/store/date-run', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/store/date-run')>()
  return { ...actual, runSnippet: hoisted.runSnippet }
})
vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

import { mount } from '@vue/test-utils'
import { parseSidecarOutput } from '../../src/sidecar-result'
import { interactiveToolSchemas, type InteractiveToolSchema } from '../../src/interactive-tools'
import { toolValues } from '../../src/store/interactive'
import { selectedId } from '../../src/store/detail'
import InteractiveToolPage from '../interactive/InteractiveToolPage.vue'

const QUICK: InteractiveToolSchema = {
  id: 'interactive:t-quick',
  title: '速查假想',
  description: '测试 quickRun。',
  tags: [],
  fields: [],
  computeVia: 'sidecar',
  quickRun: true,
  compute: () => ({}),
  pyCode: () => 'print(1)\n'
}
const WIZARD: InteractiveToolSchema = {
  id: 'interactive:t-wizard',
  title: '向导假想',
  description: '测试步骤导航。',
  tags: [],
  fields: [
    { key: 'a', label: '甲', type: 'text', default: 'A' },
    { key: 'b', label: '乙', type: 'text', default: 'B' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '第一步', keys: ['a'] },
    { title: '第二步', keys: ['b'] }
  ],
  compute: () => ({}),
  pyCode: () => 'print(2)\n'
}

beforeEach(() => {
  if (!interactiveToolSchemas.find((s) => s.id === QUICK.id)) interactiveToolSchemas.push(QUICK)
  if (!interactiveToolSchemas.find((s) => s.id === WIZARD.id)) interactiveToolSchemas.push(WIZARD)
  toolValues.value = {}
  selectedId.value = null
  hoisted.runSnippet.mockClear()
})

describe('parseSidecarOutput', () => {
  it('提取标记间 JSON，标记外文本归 rest', () => {
    const { result, rest } = parseSidecarOutput('进度行…\n<<<JSON>>>\n{"primary":{"value":"5"}}\n<<<END>>>\n尾行')
    expect(result?.primary?.value).toBe('5')
    expect(rest).toContain('进度行')
    expect(rest).not.toContain('<<<JSON>>>')
  })
  it('无标记/坏 JSON → result 为 null 且不抛错', () => {
    expect(parseSidecarOutput('纯文本输出').result).toBeNull()
    expect(parseSidecarOutput('<<<JSON>>>\n{broken\n<<<END>>>').result).toBeNull()
  })
  it('解析 table 形态', () => {
    const { result } = parseSidecarOutput('<<<JSON>>>\n{"table":{"columns":["A"],"rows":[["1"]]}}\n<<<END>>>')
    expect(result?.table?.rows).toEqual([['1']])
  })
})

describe('quickRun 自动运行', () => {
  it('进页自动运行一次（切走再切回只跑一次/每次进入各一次）', async () => {
    selectedId.value = QUICK.id
    let w = mount(InteractiveToolPage)
    await vi.waitFor(() => expect(hoisted.runSnippet).toHaveBeenCalledWith(QUICK.id, 'print(1)\n'))
    w.unmount()

    selectedId.value = 'tools_other'
    w = mount(InteractiveToolPage)
    w.unmount()
    selectedId.value = QUICK.id
    w = mount(InteractiveToolPage)
    await vi.waitFor(() => expect(hoisted.runSnippet).toHaveBeenCalledTimes(2))
    w.unmount()
  })
  it('非 quickRun 工具不自动运行', () => {
    selectedId.value = WIZARD.id
    mount(InteractiveToolPage)
    expect(hoisted.runSnippet).not.toHaveBeenCalled()
  })
})

describe('向导步骤', () => {
  it('首步只渲染本步字段；下一步进入末步出现运行', async () => {
    selectedId.value = WIZARD.id
    const w = mount(InteractiveToolPage)
    expect(w.findAll('input')).toHaveLength(1)
    await w.find('[data-testid="wizard-next"]').trigger('click')
    expect(w.findAll('input')).toHaveLength(1)
    expect(w.find('[data-testid="wizard-run"]').exists()).toBe(true)
    await w.find('[data-testid="wizard-prev"]').trigger('click')
    expect(w.find('[data-testid="wizard-run"]').exists()).toBe(false)
  })
})

describe('sidecar 结果渲染', () => {
  it('runOutput 命中标记 → 表格渲染；运行中态显示', async () => {
    selectedId.value = QUICK.id
    const w = mount(InteractiveToolPage)
    // 直接驱动 store（mock 的 date-run 保真实 refs；页面无需点击——sidecar 区随 runOutput 渲染）
    const dateRun = await import('../../src/store/date-run')
    dateRun.runBusy.value = true
    dateRun.runOutput.value =
      '加载中\n<<<JSON>>>\n{"table":{"columns":["挂载点","用"],"rows":[["/","10G"]]}}\n<<<END>>>'
    dateRun.runBusy.value = false
    await vi.waitFor(() => {
      expect(w.find('[data-testid="tool-table"]').exists()).toBe(true)
    })
    expect(w.find('[data-testid="tool-table"]').text()).toContain('10G')
    expect(w.find('[data-testid="sidecar-rest"]').text()).toContain('加载中')
  })
})
