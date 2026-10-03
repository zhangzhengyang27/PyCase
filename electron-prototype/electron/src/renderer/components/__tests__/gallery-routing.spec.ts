// 画廊路由终局（用户拍板 A + 全画廊接入）：凡交互页已覆盖能力的条目，
// openDetail 一律直达交互页面——画廊卡片 / 收藏 / 历史 / 命令面板全走此收口。
// 覆盖：viz 变体 → 图族页（含 d1~d12 模式预选）、无页面图族兜底详情页、
// CLI 标题表路由、runFromCard/retryParseArgs 绕行、交互页「查看原示例源码」回链往返。
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

import { flushPromises, mount } from '@vue/test-utils'
import InteractiveToolPage from '../interactive/InteractiveToolPage.vue'
import GalleryView from '../GalleryView.vue'
import ExampleCard from '../ExampleCard.vue'
import { examples, type VExample } from '../../src/store/catalog'
import {
  interactiveSourceId,
  openDetail,
  pendingVizMode,
  selectedId
} from '../../src/store/detail'
import { getToolSchema } from '../../src/interactive-tools'
import { toolValues } from '../../src/store/interactive'

function vizExample(family: string, n: number, overrides: Partial<VExample> = {}): VExample {
  return {
    id: `topics_viz-${family}-d${n}`,
    name: `${family}_d${n}.py`,
    category: 'topics',
    path: `bulk_viz/${family}_d${n}.py`,
    code: 'print(1)\n',
    title: '示例图族（数据形态）',
    description: '示例描述',
    tags: ['数据可视化', 'matplotlib'],
    quality_score: 80,
    run_status: 'runnable',
    ...overrides
  }
}

beforeEach(() => {
  examples.value = []
  selectedId.value = null
  interactiveSourceId.value = null
  pendingVizMode.value = null
  toolValues.value = {}
  window.confirm = () => true
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('画廊路由收口（openDetail）', () => {
  it('viz 变体卡片点击 → 直达图族交互页，记住来源卡片并预选数据模式', async () => {
    examples.value = [vizExample('bar', 8, { title: '柱状图（双峰分布）' })]
    await openDetail('topics_viz-bar-d8')
    expect(selectedId.value).toBe('interactive:viz-bar')
    expect(interactiveSourceId.value).toBe('topics_viz-bar-d8')
    expect(pendingVizMode.value).toEqual({ pageId: 'interactive:viz-bar', mode: 'bimodal' })
  })

  it('d1~d12 序号与数据模式一一对应（与生成器同序）', async () => {
    const pairs: Array<[number, string]> = [
      [1, 'sine'],
      [6, 'pulse'],
      [10, 'spike'],
      [12, 'square']
    ]
    for (const [n, mode] of pairs) {
      examples.value = [vizExample('stem', n)]
      await openDetail(`topics_viz-stem-d${n}`)
      expect(pendingVizMode.value).toEqual({ pageId: 'interactive:viz-stem', mode })
    }
  })

  it('无页面图族（quiver）不路由：留在原详情页', async () => {
    examples.value = [vizExample('quiver', 3)]
    await openDetail('topics_viz-quiver-d3')
    expect(selectedId.value).toBe('topics_viz-quiver-d3')
    expect(interactiveSourceId.value).toBeNull()
  })

  it('CLI 标题表条目同样直达交互页（W14 意图补全到画廊）', async () => {
    examples.value = [vizExample('bar', 1, { id: 'e-cli', name: 'regex.py', title: '正则测试器' })]
    await openDetail('e-cli')
    expect(selectedId.value).toBe('interactive:regex-tester')
    expect(interactiveSourceId.value).toBe('e-cli')
    expect(pendingVizMode.value).toBeNull()
  })

  it('runFromCard 绕行路由：运行的是示例文件本身', async () => {
    examples.value = [vizExample('bar', 2)]
    const { runFromCard } = await import('../../src/store/detail')
    await runFromCard('topics_viz-bar-d2')
    expect(selectedId.value).toBe('topics_viz-bar-d2')
    expect(interactiveSourceId.value).toBeNull()
  })

  it('同图族换变体重路由：同页不换 selectedId，但预选与回链更新', async () => {
    examples.value = [vizExample('bar', 5), vizExample('bar', 12)]
    await openDetail('topics_viz-bar-d5')
    expect(selectedId.value).toBe('interactive:viz-bar')
    await openDetail('topics_viz-bar-d12')
    expect(selectedId.value).toBe('interactive:viz-bar')
    expect(interactiveSourceId.value).toBe('topics_viz-bar-d12')
    expect(pendingVizMode.value).toEqual({ pageId: 'interactive:viz-bar', mode: 'square' })
  })

  it('画廊卡片点击端到端：GalleryView → openDetail → 交互页 id', async () => {
    examples.value = [vizExample('violin', 4)]
    const w = mount(GalleryView)
    await w.findAllComponents(ExampleCard)[0].get('[role="button"]').trigger('click')
    expect(selectedId.value).toBe('interactive:viz-violin')
    w.unmount()
  })
})

describe('交互页回链与模式预选（InteractiveToolPage）', () => {
  it('落页消费预选：viz 桶 mode 被置为变体对应模式并清空 pending', async () => {
    examples.value = [vizExample('box', 9)]
    await openDetail('topics_viz-box-d9')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(toolValues.value['interactive:viz-box']?.mode).toBe('sawtooth')
    expect(pendingVizMode.value).toBeNull()
    w.unmount()
  })

  it('渲染「查看原示例源码」回链，点击回到被点卡片（forceDetail 防回弹）', async () => {
    examples.value = [vizExample('radar', 7, { title: '雷达图（阶梯平台）' })]
    await openDetail('topics_viz-radar-d7')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    const btn = w.find('[data-testid="it-source"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('查看原示例源码')
    await btn.trigger('click')
    await flushPromises()
    expect(selectedId.value).toBe('topics_viz-radar-d7')
    w.unmount()
  })

  it('工具箱直开（openInteractive）无回链语境：不渲染回链按钮', async () => {
    const { openInteractive } = await import('../../src/store/interactive')
    examples.value = [vizExample('bar', 1)]
    openInteractive('interactive:viz-bar')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.find('[data-testid="it-source"]').exists()).toBe(false)
    w.unmount()
  })
})

describe('图族表完整性（防生成器改名漂移）', () => {
  it('24 个 viz schema 全部注册且 id 与图族表一致', async () => {
    const { VIZ_FAMILY_TO_INTERACTIVE } = await import('../../src/interactive-mapping')
    const vizIds = new Set(
      Object.values(VIZ_FAMILY_TO_INTERACTIVE)
        .filter((id) => id.startsWith('interactive:viz-'))
    )
    for (const id of vizIds) {
      expect(getToolSchema(id), `图族表引用了未注册页面 ${id}`).toBeTruthy()
    }
    expect(vizIds.size).toBe(24)
  })
})
