// 画廊变体归并层（唯一形态，无开关）：已路由家族折叠为单张家族卡，搜索穿透变体、favOnly 绕过、
// 未路由家族不折叠、点击家族卡照常路由进实验室（类型预选）。
import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import GalleryView from '../GalleryView.vue'
import ExampleCard from '../ExampleCard.vue'
import { mergeVariantCards } from '../../src/gallery-merge'
import {
  examples,
  favOnly,
  galleryPool,
  loadError,
  loading,
  searchQuery,
  type VExample
} from '../../src/store/catalog'
import { selectedId, openDetail, pendingPreset } from '../../src/store/detail'

function ex(id: string, overrides: Partial<VExample> = {}): VExample {
  return {
    id,
    name: `${id}.py`,
    category: 'topics',
    path: `/tmp/${id}.py`,
    code: 'print(1)\n',
    title: id,
    description: '示例描述',
    tags: ['数据可视化'],
    quality_score: 80,
    run_status: 'runnable',
    ...overrides
  }
}

const barVariants = (): VExample[] =>
  Array.from({ length: 12 }, (_, i) =>
    ex(`topics_viz-bar-d${i + 1}`, { title: `柱状图（变体${i + 1}）`, quality_score: 50 + i })
  )

beforeEach(() => {
  examples.value = []
  favOnly.value = false
  searchQuery.value = ''
  selectedId.value = null
  pendingPreset.value = null
  loading.value = false
  loadError.value = ''
})

describe('mergeVariantCards（纯函数）', () => {
  it('12 个柱状图变体折叠为 1 张家族卡：×12、标题为类型名、代表为母本 d1', () => {
    const merged = mergeVariantCards(barVariants())
    expect(merged).toHaveLength(1)
    expect(merged[0]!.variantCount).toBe(12)
    expect(merged[0]!.title).toBe('柱状图')
    expect(merged[0]!.id).toBe('topics_viz-bar-d1')
  })

  it('未路由家族（游戏）与 CLI 工具不折叠，独立单例原样通过', () => {
    const merged = mergeVariantCards([
      ...Array.from({ length: 5 }, (_, i) => ex(`topics_game-snake-${i + 1}`)),
      ex('e-cli', { title: '正则测试器' }),
      ex('topics_basics-dataclass')
    ])
    expect(merged).toHaveLength(7)
    expect(merged.every((e) => !e.variantCount)).toBe(true)
  })

  it('幂等：对已折叠池重复调用不变', () => {
    const once = mergeVariantCards(barVariants())
    expect(mergeVariantCards(once)).toEqual(once)
  })

  it('家族卡占首个成员位置（保序）', () => {
    const merged = mergeVariantCards([ex('e-other'), ...barVariants(), ex('e-tail')])
    expect(merged[0]!.id).toBe('e-other')
    expect(merged[1]!.variantCount).toBe(12)
    expect(merged[2]!.id).toBe('e-tail')
  })
})

describe('画廊集成（catalog 管道 + 开关）', () => {
  it('默认开启归并：页头统计池显示家族卡数量', () => {
    examples.value = [...barVariants(), ex('e-unique')]
    expect(galleryPool.value).toHaveLength(2)
  })

  it('单例家族透传不改写（count=1 不加归并标记）', () => {
    examples.value = [ex('topics_basics-dataclass'), ex('e-unique')]
    expect(galleryPool.value).toHaveLength(2)
    expect(galleryPool.value.every((e) => !e.variantCount)).toBe(true)
  })

  it('搜索穿透变体：搜「变体7」仍命中柱状图家族卡', () => {
    examples.value = [...barVariants(), ex('e-unique', { title: '别的示例' })]
    searchQuery.value = '变体7'
    return import('../../src/store/catalog').then(({ filtered }) => {
      expect(filtered.value.some((e) => e.variantCount === 12)).toBe(true)
    })
  })

  it('favOnly 绕过归并：收藏的变体逐张显示', async () => {
    const { favorites } = await import('../../src/store/prefs')
    examples.value = barVariants()
    favorites.value = new Set(['topics_viz-bar-d3', 'topics_viz-bar-d7'])
    favOnly.value = true
    const { filtered } = await import('../../src/store/catalog')
    expect(filtered.value).toHaveLength(2)
    favOnly.value = false
  })

  it('点击家族卡端到端：路由进实验室并预选类型与模式', async () => {
    examples.value = [...barVariants()]
    const w = mount(GalleryView)
    await flushPromises()
    const cards = w.findAllComponents(ExampleCard)
    expect(cards).toHaveLength(1)
    // 用户反馈：×N 徽章没必要——家族卡只以标题「柱状图」示人
    expect(cards[0]!.text()).toContain('柱状图')
    expect(cards[0]!.text()).not.toContain('×12')
    await cards[0]!.get('[role="button"]').trigger('click')
    expect(selectedId.value).toBe('interactive:viz-lab')
    expect(pendingPreset.value?.values).toEqual({ type: 'bar', mode: 'sine' })
    w.unmount()
  })

  it('家族卡点运行按钮：运行代表变体文件本身（不被路由改道）', async () => {
    examples.value = [...barVariants()]
    const w = mount(GalleryView)
    await flushPromises()
    await w.findAllComponents(ExampleCard)[0].find('[data-testid="card-run"]').trigger('click')
    await flushPromises()
    expect(selectedId.value).toBe('topics_viz-bar-d1')
    w.unmount()
  })
})
