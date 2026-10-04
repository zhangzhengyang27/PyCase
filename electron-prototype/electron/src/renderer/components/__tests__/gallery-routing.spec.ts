// 画廊路由终局 + 变体归并实验室（用户拍板 A + 「变体合并为单页」）：
// openDetail 统一收口 → 实验室页（fields 随类型联动）+ 类型/数据模式预选。
// 覆盖：四大实验室路由预选、无页面家族兜底、CLI 标题表、runFromCard 绕行、
// 回链往返、动态表单切换类型、映射表完整性（引用页面必须已注册 + 类型必须存在）。
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
import { interactiveSourceId, openDetail, pendingPreset, selectedId } from '../../src/store/detail'
import { getToolSchema } from '../../src/interactive-tools'
import { toolValues } from '../../src/store/interactive'
import { TOPICS_FAMILY_TO_INTERACTIVE, VIZ_FAMILY_TO_INTERACTIVE } from '../../src/interactive-mapping'

function makeExample(overrides: Partial<VExample> = {}): VExample {
  return {
    id: 'e1',
    name: 'demo.py',
    category: 'topics',
    path: '/tmp/demo.py',
    code: 'print(1)\n',
    title: '示例标题',
    description: '示例描述',
    tags: ['数据可视化'],
    quality_score: 80,
    run_status: 'runnable',
    ...overrides
  }
}

const vizExample = (family: string, n: number, title = '示例图族') =>
  makeExample({ id: `topics_viz-${family}-d${n}`, name: `${family}_d${n}.py`, title })

beforeEach(() => {
  examples.value = []
  selectedId.value = null
  interactiveSourceId.value = null
  pendingPreset.value = null
  toolValues.value = {}
  window.confirm = () => true
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('画廊路由收口（openDetail → 实验室页）', () => {
  it('viz 变体 → 图表实验室：预选类型 + 数据模式', async () => {
    examples.value = [vizExample('bar', 8, '柱状图（双峰分布）')]
    await openDetail('topics_viz-bar-d8')
    expect(selectedId.value).toBe('interactive:viz-lab')
    expect(interactiveSourceId.value).toBe('topics_viz-bar-d8')
    expect(pendingPreset.value).toEqual({
      pageId: 'interactive:viz-lab',
      values: { type: 'bar', mode: 'bimodal' }
    })
  })

  it('d1~d12 序号与数据模式一一对应', async () => {
    const pairs: Array<[number, string]> = [
      [1, 'sine'],
      [6, 'pulse'],
      [10, 'spike'],
      [12, 'square']
    ]
    for (const [n, mode] of pairs) {
      examples.value = [vizExample('stem', n)]
      await openDetail(`topics_viz-stem-d${n}`)
      expect(pendingPreset.value?.values.mode).toBe(mode)
    }
  })

  it('pil/opencv/turtle 变体 → 对应实验室并预选类型', async () => {
    examples.value = [
      makeExample({ id: 'topics_pil-gaussian-v7', name: 'gaussian_v7.py', title: '高斯模糊' }),
      makeExample({ id: 'topics_opencv-canny-s4', name: 'canny_s4.py', title: 'Canny 边缘' }),
      makeExample({ id: 'topics_turtle-spiral-v3', name: 'spiral_v3.py', title: '渐变螺旋' })
    ]
    await openDetail('topics_pil-gaussian-v7')
    expect(selectedId.value).toBe('interactive:pil-lab')
    expect(pendingPreset.value?.values).toEqual({ type: 'gaussian' })
    await openDetail('topics_opencv-canny-s4')
    expect(selectedId.value).toBe('interactive:cv-lab')
    expect(pendingPreset.value?.values).toEqual({ type: 'canny' })
    await openDetail('topics_turtle-spiral-v3')
    expect(selectedId.value).toBe('interactive:turtle-lab')
    expect(pendingPreset.value?.values).toEqual({ type: 'spiral' })
  })

  it('无页面家族（quiver）不路由；游戏家族路由进游戏实验室', async () => {
    examples.value = [
      makeExample({ id: 'topics_viz-quiver-d3', name: 'quiver_d3.py' }),
      makeExample({ id: 'topics_game-snake-1', name: 'snake_1.py' })
    ]
    await openDetail('topics_viz-quiver-d3')
    expect(selectedId.value).toBe('topics_viz-quiver-d3')
    await openDetail('topics_game-snake-1')
    expect(selectedId.value).toBe('interactive:games-lab')
    expect(pendingPreset.value?.values).toEqual({ type: 'snake' })
  })

  it('CLI 标题表条目直达交互页（无类型预选）', async () => {
    examples.value = [makeExample({ id: 'e-cli', name: 'regex.py', title: '正则测试器' })]
    await openDetail('e-cli')
    expect(selectedId.value).toBe('interactive:regex-tester')
    expect(pendingPreset.value).toBeNull()
  })

  it('runFromCard 绕行路由：运行示例文件本身', async () => {
    examples.value = [vizExample('bar', 2)]
    const { runFromCard } = await import('../../src/store/detail')
    await runFromCard('topics_viz-bar-d2')
    expect(selectedId.value).toBe('topics_viz-bar-d2')
    expect(interactiveSourceId.value).toBeNull()
  })

  it('画廊卡片点击端到端：GalleryView → openDetail → 实验室页', async () => {
    examples.value = [makeExample({ id: 'topics_viz-violin-d4', name: 'violin_d4.py', title: '小提琴图' })]
    const w = mount(GalleryView)
    await w.findAllComponents(ExampleCard)[0].get('[role="button"]').trigger('click')
    expect(selectedId.value).toBe('interactive:viz-lab')
    expect(pendingPreset.value?.values.type).toBe('violin')
    w.unmount()
  })
})

describe('交互页回链与预选消费（InteractiveToolPage）', () => {
  it('落页消费预选：类型与模式写入输入桶并清空 pending', async () => {
    examples.value = [vizExample('box', 9)]
    await openDetail('topics_viz-box-d9')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    const bucket = toolValues.value['interactive:viz-lab'] ?? {}
    expect(bucket.type).toBe('box')
    expect(bucket.mode).toBe('sawtooth')
    expect(pendingPreset.value).toBeNull()
    w.unmount()
  })

  it('渲染「查看原示例源码」回链，点击回到被点卡片', async () => {
    examples.value = [vizExample('radar', 7, '雷达图（阶梯平台）')]
    await openDetail('topics_viz-radar-d7')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    const btn = w.find('[data-testid="it-source"]')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    await flushPromises()
    expect(selectedId.value).toBe('topics_viz-radar-d7')
    w.unmount()
  })

  it('动态表单：未锁型进入时切换类型，参数字段联动更新', async () => {
    // 直接落页（无路由预选）= 未锁型探索形态；家族卡进入则是锁型（见下），
    // 页内不再提供类型切换，动态字段机制仍由本用例覆盖
    toolValues.value = {}
    selectedId.value = 'interactive:viz-lab'
    const w = mount(InteractiveToolPage)
    await flushPromises()
    // bar 类型无 rows 字段；切到 heatmap 后出现行/列数（类型选择器是第一个 select）
    expect(w.text()).not.toContain('行数')
    const selects = w.findAll('select')
    expect(selects.length).toBeGreaterThan(1)
    await selects[0]!.setValue('heatmap')
    await flushPromises()
    expect(w.text()).toContain('行数')
    w.unmount()
  })

  it('家族卡进入即锁型：类型选择器隐藏，参数与色板保留，页头为该类型', async () => {
    examples.value = [makeExample({ id: 'topics_turtle-burst-v2', name: 'burst_v2.py', title: '烟花绽放' })]
    await openDetail('topics_turtle-burst-v2')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.find('h1').text()).toBe('烟花绽放')
    const selects = w.findAll('select')
    expect(selects).toHaveLength(1) // 仅剩色板，图形选择器已隐藏
    expect(w.text()).toContain('线段数')
    w.unmount()
  })

  it('锁型页内同页重路由：再点同实验室另一家族卡，类型照常切换', async () => {
    examples.value = [
      makeExample({ id: 'topics_turtle-burst-v2', name: 'burst_v2.py', title: '烟花绽放' }),
      makeExample({ id: 'topics_turtle-lissajous-v3', name: 'lissajous_v3.py', title: '利萨茹曲线' })
    ]
    await openDetail('topics_turtle-burst-v2')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.find('h1').text()).toBe('烟花绽放')
    await openDetail('topics_turtle-lissajous-v3')
    await flushPromises()
    expect(w.find('h1').text()).toBe('利萨茹曲线')
    expect(toolValues.value['interactive:turtle-lab']?.type).toBe('lissajous')
    w.unmount()
  })

  it('turtle/pil/cv 家族卡落页：类型预选真正写入输入桶（实验室类型键统一为 type）', async () => {
    examples.value = [
      makeExample({ id: 'topics_turtle-lissajous-v3', name: 'lissajous_v3.py', title: '利萨茹曲线' }),
      makeExample({ id: 'topics_pil-gaussian-v2', name: 'gaussian_v2.py', title: '高斯模糊' }),
      makeExample({ id: 'topics_opencv-canny-s1', name: 'canny_s1.py', title: 'Canny 边缘' })
    ]
    await openDetail('topics_turtle-lissajous-v3')
    let w = mount(InteractiveToolPage)
    await flushPromises()
    expect(toolValues.value['interactive:turtle-lab']?.type).toBe('lissajous')
    w.unmount()
    await openDetail('topics_pil-gaussian-v2')
    w = mount(InteractiveToolPage)
    await flushPromises()
    expect(toolValues.value['interactive:pil-lab']?.type).toBe('gaussian')
    w.unmount()
    await openDetail('topics_opencv-canny-s1')
    w = mount(InteractiveToolPage)
    await flushPromises()
    expect(toolValues.value['interactive:cv-lab']?.type).toBe('canny')
    w.unmount()
  })

  it('家族卡进入实验室：页头标题/描述显示具体类型而非归并页名', async () => {
    examples.value = [makeExample({ id: 'topics_turtle-lissajous-v3', name: 'lissajous_v3.py', title: '利萨茹曲线' })]
    await openDetail('topics_turtle-lissajous-v3')
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.find('h1').text()).toBe('利萨茹曲线')
    expect(w.text()).toContain('参数方程逐段连线')
    w.unmount()
  })
})

describe('映射表完整性（防漂移）', () => {
  it('VIZ 表 30 图族全部指向图表实验室且类型存在', () => {
    const lab = getToolSchema('interactive:viz-lab')!
    const labFieldList = typeof lab.fields === 'function' ? lab.fields({}) : lab.fields
    const typeValues = labFieldList.find((f) => f.key === 'type')!.options as Array<{ value: string }>
    const valid = new Set(typeValues.map((o) => o.value))
    expect(Object.keys(VIZ_FAMILY_TO_INTERACTIVE)).toHaveLength(29)
    for (const [fam, route] of Object.entries(VIZ_FAMILY_TO_INTERACTIVE)) {
      expect(route.page, fam).toBe('interactive:viz-lab')
      expect(valid.has(route.type), `${fam} → 类型 ${route.type} 不存在`).toBe(true)
    }
  })

  it('TOPICS 表每个路由目标页面已注册、实验室类型存在', () => {
    // 路由层预选统一发 key='type'（detail.ts），实验室类型选择器 key 必须与其一致，
    // 否则预选落页被静默丢弃（历史上 turtle=shape / pil=filter / cv=op 曾各自为政）
    const labTypeFields: Record<string, string> = {
      'interactive:pil-lab': 'type',
      'interactive:cv-lab': 'type',
      'interactive:turtle-lab': 'type'
    }
    expect(Object.keys(TOPICS_FAMILY_TO_INTERACTIVE).length).toBeGreaterThanOrEqual(95)
    for (const [fam, route] of Object.entries(TOPICS_FAMILY_TO_INTERACTIVE)) {
      const schema = getToolSchema(route.page)
      expect(schema, `家族 ${fam} 引用了未注册页面 ${route.page}`).toBeTruthy()
      if (route.type && labTypeFields[route.page]) {
        const schemaFieldList = typeof schema!.fields === 'function' ? schema!.fields({}) : schema!.fields
        const typeField = schemaFieldList.find((f) => f.key === labTypeFields[route.page])
        const opts = typeField!.options as Array<{ value: string }>
        expect(opts.map((o) => o.value)).toContain(route.type)
      }
    }
  })
})
