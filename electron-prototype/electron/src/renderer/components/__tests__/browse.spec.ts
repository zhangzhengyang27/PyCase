// browse 层组件测试：画廊 / 工具箱 / 筛选侧栏——三个依赖共享 store 的「浏览」视图。
// 与 base.spec 的本质差异：这些组件从模块级单例 store 读状态，因此每个用例前必须
// 调 resetViewFilters() 归零，再按用例需要直接给导出 ref 赋值（单例状态会跨用例残留）。
// 断言优先落在渲染文本 / 类名与交互后的 store 状态上，不穿透子组件内部实现。
import { describe, expect, it, afterEach, beforeEach, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'

import GalleryView from '../GalleryView.vue'
import ToolboxView from '../ToolboxView.vue'
import FilterSidebar from '../FilterSidebar.vue'
import ExampleCard from '../ExampleCard.vue'
import ExampleListItem from '../ExampleListItem.vue'
import {
  activeCategory,
  activeRunnable,
  activeRunStatus,
  activeSectionTags,
  activeTags,
  activeTheme,
  examples,
  favOnly,
  favorites,
  galleryLimit,
  galleryMode,
  getTestApi,
  loadError,
  loading,
  minQuality,
  runHistory,
  searchQuery,
  selectedId,
  sortBy,
  toolSearchQuery,
  viewMode,
  type VExample
} from '../../store'

// GalleryView 在 onMounted 里实例化 IntersectionObserver 做触底加载；
// jsdom 未实现它，桩已由 vitest.setup.ts 统一提供。

/** 与 sidecar ExampleItem 同形的示例工厂；默认值让「不加筛选时全部可见」成立。 */
function makeExample(overrides: Partial<VExample> = {}): VExample {
  return {
    id: 'e1',
    name: 'demo.py',
    category: 'topics',
    path: '/tmp/demo.py',
    code: 'print(1)\n',
    description: '示例描述',
    tags: ['基础'],
    quality_score: 80,
    run_status: 'runnable',
    ...overrides
  }
}

const testApi = getTestApi() as unknown as { resetViewFilters: () => void }

beforeEach(() => {
  // store 是单例：不归零则上一个用例的筛选/搜索会串进下一个。
  testApi.resetViewFilters()
  examples.value = []
  loading.value = false
  loadError.value = ''
  viewMode.value = 'grid'
  galleryLimit.value = 120
  sortBy.value = 'quality_desc'
  favorites.value = new Set()
  runHistory.value = []
  selectedId.value = null
  // openDetail 切换选中项时会调 window.confirm；jsdom 的实现会打印 not implemented 噪音。
  window.confirm = () => true
})

afterEach(() => {
  document.body.innerHTML = ''
})

// ---------------------------------------------------------------------------
// GalleryView
// ---------------------------------------------------------------------------
describe('GalleryView', () => {
  // 根 <section> 下恰有两个面板 div：总览态 / 浏览态（v-show 切换，二者始终在 DOM 里）。
  // 取 children 而非宽松选择器：避免命中面板内部的同名结构。
  function panels(w: VueWrapper) {
    const kids = w.element.children
    return { overview: kids[0] as HTMLElement, browse: kids[1] as HTMLElement }
  }

  it('总览态加载中且无示例时渲染 8 个骨架卡', () => {
    loading.value = true
    const w = mount(GalleryView)
    expect(panels(w).overview.querySelectorAll('.animate-pulse')).toHaveLength(8)
  })

  it('总览态加载失败时显示错误横幅，重试按钮 emit reload', async () => {
    loadError.value = 'sidecar 连接失败'
    const w = mount(GalleryView)
    const { overview } = panels(w)
    expect(overview.textContent).toContain('加载失败: sidecar 连接失败')

    const retry = Array.from(overview.querySelectorAll('button')).find((b) => b.textContent!.includes('重试'))!
    retry.click()
    await w.vm.$nextTick()
    expect(w.emitted('reload')).toHaveLength(1)
  })

  it('总览态无示例时展示空态文案', () => {
    const w = mount(GalleryView)
    expect(panels(w).overview.textContent).toContain('示例库为空')
  })

  it('总览态有示例时渲染 GalleryOverview（标题与统计），不残留骨架', () => {
    examples.value = [makeExample({ id: 'a', name: 'turtle_draw.py', code: 'import turtle\n', tags: ['基础'] })]
    const w = mount(GalleryView)
    const { overview } = panels(w)
    expect(overview.querySelector('h1')?.textContent).toBe('示例库')
    expect(overview.textContent).toContain('个示例')
    expect(overview.querySelectorAll('.animate-pulse')).toHaveLength(0)
  })

  it('galleryMode 决定两个面板的可见性（互斥的 v-show）', async () => {
    examples.value = [makeExample()]
    const w = mount(GalleryView)
    expect(panels(w).overview.style.display).not.toBe('none')
    expect(panels(w).browse.style.display).toBe('none')

    galleryMode.value = 'browse'
    await w.vm.$nextTick()
    expect(panels(w).overview.style.display).toBe('none')
    expect(panels(w).browse.style.display).not.toBe('none')
  })

  it('浏览态加载中且无示例时渲染 8 个骨架卡', () => {
    galleryMode.value = 'browse'
    loading.value = true
    const w = mount(GalleryView)
    expect(panels(w).browse.querySelectorAll('.animate-pulse')).toHaveLength(8)
  })

  it('浏览态加载失败时展示错误横幅与重试按钮', async () => {
    galleryMode.value = 'browse'
    loadError.value = '超时'
    const w = mount(GalleryView)
    const { browse } = panels(w)
    expect(browse.textContent).toContain('加载失败: 超时')

    const retry = Array.from(browse.querySelectorAll('button')).find((b) => b.textContent!.includes('重试'))!
    retry.click()
    await w.vm.$nextTick()
    expect(w.emitted('reload')).toHaveLength(1)
  })

  it('浏览态筛选无结果时展示空态而非卡片', () => {
    galleryMode.value = 'browse'
    examples.value = [makeExample({ id: 'a', tags: ['基础'] })]
    activeTags.value = new Set(['不存在的标签'])
    const w = mount(GalleryView)
    const { browse } = panels(w)
    expect(browse.textContent).toContain('没有匹配的示例')
    expect(browse.querySelectorAll('.surface-card')).toHaveLength(0)
  })

  it('浏览态默认网格密度：卡片数等于 shownGallery，且不渲染列表项', () => {
    galleryMode.value = 'browse'
    examples.value = [
      makeExample({ id: 'a', name: 'a.py', quality_score: 90 }),
      makeExample({ id: 'b', name: 'b.py', quality_score: 70 }),
      makeExample({ id: 'c', name: 'c.py', quality_score: 50 })
    ]
    const w = mount(GalleryView)
    expect(panels(w).browse.querySelectorAll('.surface-card')).toHaveLength(3)
    expect(w.findAllComponents(ExampleListItem)).toHaveLength(0)
  })

  it('浏览态切换为清单密度后渲染列表项而非卡片', () => {
    galleryMode.value = 'browse'
    viewMode.value = 'list'
    examples.value = [makeExample({ id: 'a', name: 'a.py' }), makeExample({ id: 'b', name: 'b.py' })]
    const w = mount(GalleryView)
    expect(w.findAllComponents(ExampleListItem)).toHaveLength(2)
    expect(panels(w).browse.querySelectorAll('.surface-card')).toHaveLength(0)
  })

  it('浏览态卡片数受 galleryLimit 截断', () => {
    galleryMode.value = 'browse'
    galleryLimit.value = 2
    examples.value = [1, 2, 3, 4, 5].map((i) => makeExample({ id: `e${i}`, name: `e${i}.py`, quality_score: i }))
    const w = mount(GalleryView)
    expect(panels(w).browse.querySelectorAll('.surface-card')).toHaveLength(2)
  })

  it('点击网格卡片经 openDetail 打开对应示例详情', async () => {
    galleryMode.value = 'browse'
    // 质量分降序：hi 排在首位，点第一张卡应命中 hi
    examples.value = [
      makeExample({ id: 'hi', name: 'hi.py', quality_score: 90 }),
      makeExample({ id: 'lo', name: 'lo.py', quality_score: 10 })
    ]
    const w = mount(GalleryView)
    const firstCard = panels(w).browse.querySelector('.surface-card') as HTMLElement
    firstCard.click()
    await w.vm.$nextTick()
    expect(selectedId.value).toBe('hi')
  })

  it('点击卡片星标切换该示例收藏状态（不触发行打开）', async () => {
    galleryMode.value = 'browse'
    examples.value = [makeExample({ id: 'hi', name: 'hi.py', quality_score: 90 })]
    const w = mount(GalleryView)
    const star = panels(w).browse.querySelector('button[title="收藏"]') as HTMLElement
    star.click()
    await w.vm.$nextTick()
    expect(favorites.value.has('hi')).toBe(true)
    expect(selectedId.value).toBeNull()
  })

  it('浏览态结果条展示筛选芯片，点「清空」调用 clearAllFilters 归零全部筛选', async () => {
    galleryMode.value = 'browse'
    examples.value = [makeExample({ id: 'a', name: 'turtle_draw.py', code: 'import turtle\n' })]
    activeTheme.value = 'turtle'
    minQuality.value = 80
    favOnly.value = true
    const w = mount(GalleryView)
    const { browse } = panels(w)
    expect(browse.textContent).toContain('Turtle 绘图')
    expect(browse.textContent).toContain('质量分 ≥80')
    expect(browse.textContent).toContain('我的收藏')

    const clear = Array.from(browse.querySelectorAll('button')).find((b) => b.textContent!.trim() === '清空')!
    clear.click()
    await w.vm.$nextTick()
    expect(activeTheme.value).toBe('all')
    expect(minQuality.value).toBe(0)
    expect(favOnly.value).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// ToolboxView
// ---------------------------------------------------------------------------
describe('ToolboxView', () => {
  // 9 个工具：7 个属同一项目（触发「展开全部」折叠）、1 个另一项目、1 个无 source_dir（独立工具）
  function toolFixtures(): VExample[] {
    const big = Array.from({ length: 7 }, (_, i) =>
      makeExample({
        id: `c${i}`,
        name: `crawler_${i}.py`,
        category: 'tools',
        source_dir: 'tools/utility-crawlers',
        quality_score: 90 - i
      })
    )
    const other = makeExample({
      id: 'bm',
      name: 'black_magic.py',
      category: 'tools',
      source_dir: 'tools/python-black-magic',
      quality_score: 60
    })
    const standalone = makeExample({ id: 'sa', name: 'standalone_tool.py', category: 'tools', quality_score: 50 })
    return [...big, other, standalone]
  }

  function groupSection(w: VueWrapper, label: string) {
    return w.findAll('section.mb-9').find((s) => s.find('h2').exists() && s.find('h2').text() === label)!
  }

  it('加载中且无示例时渲染 8 个骨架卡', () => {
    loading.value = true
    const w = mount(ToolboxView)
    expect(w.findAll('.animate-pulse')).toHaveLength(8)
  })

  it('加载失败时显示错误横幅，重试按钮 emit reload', async () => {
    loadError.value = 'sidecar 连接失败'
    const w = mount(ToolboxView)
    expect(w.text()).toContain('加载失败: sidecar 连接失败')

    const retry = w.findAll('button').find((b) => b.text().includes('重试'))!
    await retry.trigger('click')
    expect(w.emitted('reload')).toHaveLength(1)
  })

  it('没有工具时展示空态文案', () => {
    // 只有非 tools 类目：工具箱池为空（画廊池非空，证明空态来自工具池而非示例为空）
    examples.value = [makeExample({ id: 't', category: 'topics' })]
    const w = mount(ToolboxView)
    expect(w.text()).toContain('没有匹配的工具')
  })

  it('工具池为空时页头仍然可见——它是退出筛选的唯一入口', () => {
    examples.value = [makeExample({ id: 't', category: 'topics' })]
    const w = mount(ToolboxView)

    expect(w.text()).toContain('没有匹配的工具')
    // 回归：空态曾整块替换页头，用户因此无法清空搜索词或关掉「只看收藏」，被永久困住
    expect(w.find('input[placeholder="搜索工具…"]').exists()).toBe(true)
    expect(w.find('select').exists()).toBe(true)
    expect(w.findAll('button').some((b) => b.attributes('aria-label') === '只看收藏')).toBe(true)
  })

  it('空态归因于收藏筛选，而不是一律怪搜索词', () => {
    examples.value = toolFixtures()
    favorites.value = new Set()
    favOnly.value = true
    const w = mount(ToolboxView)

    expect(w.text()).toContain('没有匹配的工具')
    expect(w.text()).toContain('当前只显示已收藏的工具')
    expect(w.text()).not.toContain('调整搜索词试试')
  })

  it('搜索无匹配时空态归因于搜索词', async () => {
    examples.value = toolFixtures()
    // 搜索是防抖的：toolSearchQuery 输入后 120ms 才写入 appliedToolSearch（toolboxItems 用的是后者）
    vi.useFakeTimers()
    toolSearchQuery.value = 'zzz-不存在'
    await nextTick()
    vi.advanceTimersByTime(120)
    await nextTick()
    vi.useRealTimers()

    const w = mount(ToolboxView)
    expect(w.findAll('section.mb-9')).toHaveLength(0)
    expect(w.text()).toContain('没有匹配的工具')
    expect(w.text()).toContain('调整搜索词试试')
  })

  it('空态下点星标即可退出「只看收藏」，列表随即恢复', async () => {
    examples.value = toolFixtures()
    favorites.value = new Set()
    favOnly.value = true
    const w = mount(ToolboxView)
    expect(w.findAll('section.mb-9')).toHaveLength(0)

    // 开关处于激活态时，按钮的 aria-label 会翻转为「显示全部工具」
    const toggle = w.findAll('button').find((b) => b.attributes('aria-label') === '显示全部工具')!
    await toggle.trigger('click')

    expect(favOnly.value).toBe(false)
    expect(w.findAll('section.mb-9').length).toBeGreaterThan(0)
  })

  it('页头统计工具数 / 项目数 / 可静态运行百分比', () => {
    examples.value = toolFixtures()
    const w = mount(ToolboxView)
    expect(w.text()).toContain('9 个工具 · 2 个工具项目 · 100% 可静态运行')
  })

  it('按 source_dir 分组：内置项目用中文区名、按声明序排列，无 source_dir 归入独立工具', () => {
    examples.value = toolFixtures()
    const w = mount(ToolboxView)
    expect(w.findAll('section.mb-9 h2').map((h) => h.text())).toEqual(['Python 黑魔法', '实用爬虫合集', '独立工具'])
  })

  it('大项目默认只露前 6 张卡，可「展开全部」再「收起」', async () => {
    examples.value = toolFixtures()
    const w = mount(ToolboxView)
    expect(groupSection(w, '实用爬虫合集').findAllComponents(ExampleCard)).toHaveLength(6)

    const toggle = groupSection(w, '实用爬虫合集')
      .findAll('button')
      .find((b) => b.text().includes('展开全部'))!
    expect(toggle.text()).toContain('展开全部 1 个')

    await toggle.trigger('click')
    expect(groupSection(w, '实用爬虫合集').findAllComponents(ExampleCard)).toHaveLength(7)
    expect(groupSection(w, '实用爬虫合集').text()).toContain('收起')
  })

  it('搜索词非空时强制全展开（无需点展开按钮，避免命中项被折叠藏住）', () => {
    examples.value = toolFixtures()
    toolSearchQuery.value = 'crawler'
    const w = mount(ToolboxView)
    const big = groupSection(w, '实用爬虫合集')
    expect(big.findAllComponents(ExampleCard)).toHaveLength(7)
    expect(big.text()).toContain('收起')
  })

  it('点击工具卡片经 openDetail 打开详情', async () => {
    examples.value = [makeExample({ id: 'only', name: 'only_tool.py', category: 'tools' })]
    const w = mount(ToolboxView)
    await w.find('.surface-card').trigger('click')
    expect(selectedId.value).toBe('only')
  })

  it('收藏按钮切换 favOnly，并反映到 title 与 aria-pressed', async () => {
    examples.value = toolFixtures()
    // 预置一个收藏：否则开启 favOnly 后工具池为空、页头会被空态分支替换，按钮消失
    favorites.value = new Set(['c0'])
    const w = mount(ToolboxView)
    const favBtn = w.findAll('button').find((b) => b.attributes('title') === '只看收藏')!
    expect(favBtn.attributes('aria-pressed')).toBe('false')

    await favBtn.trigger('click')
    expect(favOnly.value).toBe(true)
    expect(w.findAll('button').find((b) => b.attributes('title') === '显示全部工具')!.attributes('aria-pressed')).toBe(
      'true'
    )
  })
})

// ---------------------------------------------------------------------------
// FilterSidebar
// ---------------------------------------------------------------------------
describe('FilterSidebar', () => {
  // 两条画廊示例：a 命中 turtle 主题 + runnable；b 命中 games 主题 + missing_deps。
  // 用于验证 facet 计数与分组维度。
  function facetFixtures(): VExample[] {
    return [
      makeExample({
        id: 'a',
        name: 'turtle_draw.py',
        code: 'import turtle\n',
        tags: ['基础'],
        quality_score: 90,
        run_status: 'runnable'
      }),
      makeExample({
        id: 'b',
        name: 'beta.py',
        code: 'import pygame\n',
        tags: ['游戏'],
        quality_score: 60,
        run_status: 'missing_deps'
      })
    ]
  }

  // 分组头按钮是唯一同时带 aria-expanded 与组名的按钮（折叠按钮文本为空，不参与匹配）。
  function groupHeader(w: VueWrapper, label: string) {
    return w
      .findAll('button')
      .find((b) => b.attributes('aria-expanded') !== undefined && b.text().includes(label))!
  }

  // 组内容 div 恒为组头按钮的下一个兄弟节点（v-show 控制显隐，节点始终在 DOM 里）。
  function groupFacets(w: VueWrapper, label: string) {
    const content = groupHeader(w, label).element.nextElementSibling as HTMLElement
    return w.findAll('button').filter((b) => content.contains(b.element))
  }

  function facetByText(w: VueWrapper, group: string, label: string) {
    return groupFacets(w, group).find((b) => (b.element.textContent || '').trim().startsWith(label))!
  }

  function groupLabels(w: VueWrapper) {
    return w
      .findAll('button')
      .filter((b) => b.attributes('aria-expanded') !== undefined)
      .map((b) => b.text())
  }

  it('gallery 作用域使用画廊搜索框文案，并渲染主题 / 质量分组', () => {
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(w.get('input').attributes('placeholder')).toBe('搜索名称 / 标签 / 代码…')
    expect(w.get('input').attributes('aria-label')).toBe('搜索示例（名称、标签、代码）')

    const labels = groupLabels(w)
    expect(labels.some((t) => t.includes('主题'))).toBe(true)
    expect(labels.some((t) => t.includes('质量分'))).toBe(true)
  })

  it('toolbox 作用域使用工具箱搜索框文案，且不渲染画廊专属分组', () => {
    const w = mount(FilterSidebar, { props: { scope: 'toolbox' } })
    expect(w.get('input').attributes('placeholder')).toBe('搜索工具…')
    expect(w.get('input').attributes('aria-label')).toBe('搜索工具')

    const labels = groupLabels(w)
    expect(labels.some((t) => t.includes('主题'))).toBe(false)
    expect(labels.some((t) => t.includes('质量分'))).toBe(false)
  })

  it('搜索框按作用域写回各自的 store ref，两个作用域互不影响', async () => {
    const gallery = mount(FilterSidebar, { props: { scope: 'gallery' } })
    await gallery.get('input').setValue('turtle')
    expect(searchQuery.value).toBe('turtle')
    expect(toolSearchQuery.value).toBe('')

    const toolbox = mount(FilterSidebar, { props: { scope: 'toolbox' } })
    await toolbox.get('input').setValue('crawler')
    expect(toolSearchQuery.value).toBe('crawler')
    // 工具箱写入不得污染画廊搜索词
    expect(searchQuery.value).toBe('turtle')
  })

  it('折叠后侧栏收窄、正文隐藏，并按激活维度数显示计数徽标', async () => {
    activeRunStatus.value = 'ok'
    activeRunnable.value = 'broken'
    activeTags.value = new Set(['x', 'y'])
    favOnly.value = true
    activeTheme.value = 'turtle'
    minQuality.value = 80
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(w.get('aside').classes()).toContain('w-[232px]')

    await w.get('aside').find('button').trigger('click')
    expect(w.get('aside').classes()).toContain('w-11')
    // v-if 移除正文：折叠后不再有「筛选」字样
    expect(w.text()).not.toContain('筛选')
    // 1(运行状态) + 1(可运行性) + 1(主题) + 1(质量分) + 2(标签) + 1(收藏) = 7
    expect(w.get('aside').text()).toContain('7')
  })

  it('运行状态 facet 点击后写入 activeRunStatus 并切换 aria-pressed', async () => {
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(facetByText(w, '运行状态', '成功过').attributes('aria-pressed')).toBe('false')

    await facetByText(w, '运行状态', '成功过').trigger('click')
    expect(activeRunStatus.value).toBe('ok')
    expect(facetByText(w, '运行状态', '成功过').attributes('aria-pressed')).toBe('true')
  })

  it('可运行性 facet 显示 facetCounts 计数；计数为 0 时不渲染计数位', () => {
    examples.value = facetFixtures()
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(facetByText(w, '可运行性', '可运行').text()).toContain('1')
    expect(facetByText(w, '可运行性', '缺依赖').text()).toContain('1')
    expect(facetByText(w, '可运行性', '空壳').text().trim()).toBe('空壳')
  })

  it('可运行性 facet 点击后写入 activeRunnable', async () => {
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    await facetByText(w, '可运行性', '缺依赖').trigger('click')
    expect(activeRunnable.value).toBe('missing_deps')
  })

  it('主题分组默认收起，展开后选主题写入 activeTheme 并持久化 viewPrefs', async () => {
    examples.value = facetFixtures()
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(groupHeader(w, '主题').attributes('aria-expanded')).toBe('false')
    expect((groupHeader(w, '主题').element.nextElementSibling as HTMLElement).style.display).toBe('none')

    await groupHeader(w, '主题').trigger('click')
    expect(groupHeader(w, '主题').attributes('aria-expanded')).toBe('true')

    await facetByText(w, '主题', 'Turtle 绘图').trigger('click')
    expect(activeTheme.value).toBe('turtle')
    expect(vi.mocked(window.sidecar.store.set)).toHaveBeenCalledWith(
      'viewPrefs',
      expect.objectContaining({ activeTheme: 'turtle' })
    )
  })

  it('质量分 facet 点击后写入 minQuality', async () => {
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    await groupHeader(w, '质量分').trigger('click')
    await facetByText(w, '质量分', '90+').trigger('click')
    expect(minQuality.value).toBe(90)
  })

  it('标签可多选：点击加入 activeTags，再点移除', async () => {
    examples.value = facetFixtures()
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    const tagRow = () => groupFacets(w, '标签').find((b) => b.attributes('title') === '基础')!

    await tagRow().trigger('click')
    expect(activeTags.value.has('基础')).toBe(true)
    await tagRow().trigger('click')
    expect(activeTags.value.has('基础')).toBe(false)
  })

  it('标签超过 10 个时只露 Top10，可展开全部再收起', async () => {
    examples.value = Array.from({ length: 12 }, (_, i) =>
      makeExample({ id: `t${i}`, name: `t${i}.py`, tags: [`tag${String(i).padStart(2, '0')}`], code: 'print(1)\n' })
    )
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    const tagRows = () => groupFacets(w, '标签').filter((b) => b.attributes('title') !== undefined)
    expect(tagRows()).toHaveLength(10)

    const expand = groupFacets(w, '标签').find((b) => b.text().includes('展开全部'))!
    expect(expand.text()).toContain('+2')
    await expand.trigger('click')
    expect(tagRows()).toHaveLength(12)
    expect(groupFacets(w, '标签').some((b) => b.text().includes('收起标签'))).toBe(true)
  })

  it('两个作用域的标签 facet 取自各自池（画廊不含工具标签）', () => {
    examples.value = [
      makeExample({ id: 'g', category: 'topics', tags: ['画廊标签'] }),
      makeExample({ id: 't', category: 'tools', tags: ['工具标签'] })
    ]
    const titles = (w: VueWrapper) =>
      groupFacets(w, '标签')
        .filter((b) => b.attributes('title') !== undefined)
        .map((b) => b.attributes('title'))

    const galleryTags = titles(mount(FilterSidebar, { props: { scope: 'gallery' } }))
    expect(galleryTags).toContain('画廊标签')
    expect(galleryTags).not.toContain('工具标签')

    const toolboxTags = titles(mount(FilterSidebar, { props: { scope: 'toolbox' } }))
    expect(toolboxTags).toContain('工具标签')
    expect(toolboxTags).not.toContain('画廊标签')
  })

  it('收藏开关切换 favOnly 并显示收藏计数', async () => {
    favorites.value = new Set(['a', 'b'])
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    const favRow = () => w.findAll('button').find((b) => b.attributes('title') === '只看收藏')!
    expect(favRow().text()).toContain('2')

    await favRow().trigger('click')
    expect(favOnly.value).toBe(true)
    expect(favRow().attributes('aria-pressed')).toBe('true')
  })

  it('有额外筛选时出现「清除筛选」，点击后除收藏 / 搜索外的维度归零', async () => {
    activeRunStatus.value = 'ok'
    activeRunnable.value = 'broken'
    activeTags.value = new Set(['基础'])
    activeTheme.value = 'turtle'
    minQuality.value = 80
    activeSectionTags.value = ['x']
    activeCategory.value = 'projects'
    favOnly.value = true
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })

    const clear = w.findAll('button').find((b) => b.text().includes('清除筛选'))!
    await clear.trigger('click')

    expect(activeRunStatus.value).toBe('all')
    expect(activeRunnable.value).toBe('all')
    expect(activeTags.value.size).toBe(0)
    expect(activeTheme.value).toBe('all')
    expect(minQuality.value).toBe(0)
    expect(activeSectionTags.value).toEqual([])
    expect(activeCategory.value).toBe('all')
    // clearFilters 不触碰收藏开关（那是 clearAllFilters 的职责）
    expect(favOnly.value).toBe(true)
  })

  it('仅有收藏开关时不渲染「清除筛选」按钮（收藏不计入额外筛选判定）', () => {
    favOnly.value = true
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(w.findAll('button').some((b) => b.text().includes('清除筛选'))).toBe(false)
  })

  it('选中的 facet 行带高亮类，未选中的不带', () => {
    activeRunStatus.value = 'ok'
    const w = mount(FilterSidebar, { props: { scope: 'gallery' } })
    expect(facetByText(w, '运行状态', '成功过').classes()).toContain('bg-accent/15')
    expect(facetByText(w, '运行状态', '全部').classes()).not.toContain('bg-accent/15')
  })
})
