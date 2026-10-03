// browse 层组件测试：画廊 / 工具箱 / 工具栏筛选下拉——依赖共享 store 的「浏览」视图。
// 与 base.spec 的本质差异：这些组件从模块级单例 store 读状态，因此每个用例前必须
// 调 resetViewFilters() 归零，再按用例需要直接给导出 ref 赋值（单例状态会跨用例残留）。
// 断言优先落在渲染文本 / 类名与交互后的 store 状态上，不穿透子组件内部实现。
import { describe, expect, it, afterEach, beforeEach, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'

import GalleryView from '../GalleryView.vue'
import ToolboxView from '../ToolboxView.vue'
import BrowseToolbar from '../BrowseToolbar.vue'
import ExampleCard from '../ExampleCard.vue'
import ExampleListItem from '../ExampleListItem.vue'
import {
  activeSectionKey,
  activeTags,
  activeTheme,
  examples,
  favOnly,
  galleryLimit,
  loadError,
  loading,
  sortBy,
  toolSearchQuery,
  viewMode,
  type VExample
} from '../../src/store/catalog'
import { selectedId } from '../../src/store/detail'
import { getTestApi } from '../../src/store/index'
import { favorites, runHistory } from '../../src/store/prefs'

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
// 单态浏览视图：页头 + 结果条（筛选维度收成工具栏下拉）+ 网格/清单。
// 独立筛选栏列与 <1100px 浮层已退役——筛选改由工具栏下拉承担。
describe('GalleryView', () => {
  it('加载中且无示例时渲染 8 个骨架卡', () => {
    loading.value = true
    const w = mount(GalleryView)
    expect(w.findAll('.animate-pulse')).toHaveLength(8)
  })

  it('加载失败时展示错误横幅与重试按钮，emit reload', async () => {
    loadError.value = 'sidecar 连接失败'
    const w = mount(GalleryView)
    expect(w.text()).toContain('加载失败: sidecar 连接失败')

    const retry = w.findAll('button').find((b) => b.text().includes('重试'))!
    await retry.trigger('click')
    expect(w.emitted('reload')).toHaveLength(1)
  })

  it('库为空时展示空态文案', () => {
    const w = mount(GalleryView)
    expect(w.text()).toContain('示例库为空')
  })

  it('有示例时渲染页头（标题与统计）与卡片网格，不残留骨架', () => {
    examples.value = [makeExample({ id: 'a', name: 'turtle_draw.py', code: 'import turtle\n', tags: ['基础'] })]
    const w = mount(GalleryView)
    expect(w.find('h1').text()).toBe('示例库')
    expect(w.text()).toContain('个示例')
    expect(w.findAllComponents(ExampleCard)).toHaveLength(1)
    expect(w.findAll('.animate-pulse')).toHaveLength(0)
  })

  it('筛选无结果时展示空态而非卡片', () => {
    examples.value = [makeExample({ id: 'a', tags: ['基础'] })]
    activeTags.value = new Set(['不存在的标签'])
    const w = mount(GalleryView)
    expect(w.text()).toContain('没有匹配的示例')
    expect(w.findAllComponents(ExampleCard)).toHaveLength(0)
  })

  it('默认网格密度：卡片数等于 shownGallery，且不渲染列表项', () => {
    examples.value = [
      makeExample({ id: 'a', name: 'a.py', quality_score: 90 }),
      makeExample({ id: 'b', name: 'b.py', quality_score: 70 }),
      makeExample({ id: 'c', name: 'c.py', quality_score: 50 })
    ]
    const w = mount(GalleryView)
    expect(w.findAllComponents(ExampleCard)).toHaveLength(3)
    expect(w.findAllComponents(ExampleListItem)).toHaveLength(0)
  })

  it('切换为清单密度后渲染列表项而非卡片', () => {
    viewMode.value = 'list'
    examples.value = [makeExample({ id: 'a', name: 'a.py' }), makeExample({ id: 'b', name: 'b.py' })]
    const w = mount(GalleryView)
    expect(w.findAllComponents(ExampleListItem)).toHaveLength(2)
    expect(w.findAllComponents(ExampleCard)).toHaveLength(0)
  })

  it('卡片数受 galleryLimit 截断', () => {
    galleryLimit.value = 2
    examples.value = [1, 2, 3, 4, 5].map((i) => makeExample({ id: `e${i}`, name: `e${i}.py`, quality_score: i }))
    const w = mount(GalleryView)
    expect(w.findAllComponents(ExampleCard)).toHaveLength(2)
  })

  it('点击网格卡片经 openDetail 打开对应示例详情', async () => {
    // 质量分降序：hi 排在首位，点第一张卡应命中 hi
    examples.value = [
      makeExample({ id: 'hi', name: 'hi.py', quality_score: 90 }),
      makeExample({ id: 'lo', name: 'lo.py', quality_score: 10 })
    ]
    const w = mount(GalleryView)
    await w.findAllComponents(ExampleCard)[0].get('[role="button"]').trigger('click')
    expect(selectedId.value).toBe('hi')
  })

  it('点击卡片星标切换该示例收藏状态（不触发行打开）', async () => {
    examples.value = [makeExample({ id: 'hi', name: 'hi.py', quality_score: 90 })]
    const w = mount(GalleryView)
    await w.getComponent(ExampleCard).get('button[title="收藏"]').trigger('click')
    expect(favorites.value.has('hi')).toBe(true)
    expect(selectedId.value).toBeNull()
  })

  it('结果条展示筛选芯片，点「清空」调用 clearAllFilters 归零全部筛选', async () => {
    examples.value = [makeExample({ id: 'a', name: 'turtle_draw.py', code: 'import turtle\n' })]
    activeTheme.value = 'turtle'
    favOnly.value = true
    const w = mount(GalleryView)
    expect(w.text()).toContain('Turtle 绘图')
    expect(w.text()).toContain('我的收藏')

    const clear = w.findAll('button').find((b) => b.text().trim() === '清空')!
    await clear.trigger('click')
    expect(activeTheme.value).toBe('all')
    expect(favOnly.value).toBe(false)
  })

  it('工具栏主题下拉驱动筛选：选后 activeTheme 写回、网格随即收敛', async () => {
    examples.value = [
      makeExample({ id: 'a', name: 'a.py', theme_key: 'turtle', quality_score: 90 }),
      makeExample({ id: 'b', name: 'b.py', theme_key: 'games', quality_score: 80 })
    ]
    const w = mount(GalleryView)
    expect(w.findAllComponents(ExampleCard)).toHaveLength(2)

    await w.get('[data-testid="filter-theme"]').trigger('click')
    await flushPromises()
    const themeItem = w.findAll('[role="menuitemradio"]').find((i) => i.text().trim().startsWith('Turtle 绘图'))!
    expect(themeItem, '主题菜单项不存在').toBeTruthy()
    await themeItem.trigger('click')
    await flushPromises()
    expect(activeTheme.value).toBe('turtle')
    expect(w.findAllComponents(ExampleCard)).toHaveLength(1)
  })

  it('新形态：不再有独立筛选栏列 / 窄窗筛选按钮 / 浮层，筛选齐备于工具栏下拉', () => {
    examples.value = [makeExample({ id: 'a', code: 'import turtle\n', tags: ['基础'] })]
    const w = mount(GalleryView)
    // 独立筛选栏列（aside）与窄窗「筛选」浮层均已退役
    expect(w.find('aside').exists()).toBe(false)
    expect(w.find('[data-testid="gallery-filter-toggle"]').exists()).toBe(false)
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
    // 工具栏下拉齐备：主题 / 可运行性 / 质量分 / 运行状态 / 标签
    expect(w.find('[data-testid="filter-theme"]').exists()).toBe(true)
    expect(w.find('[data-testid="filter-runnable"]').exists()).toBe(false)
    expect(w.find('[data-testid="filter-quality"]').exists()).toBe(false)
    expect(w.find('[data-testid="filter-run-status"]').exists()).toBe(false)
    expect(w.find('[data-testid="tag-filter-select"]').exists()).toBe(true)
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

  it('没有工具时交互工具兜底在列，收藏过滤后仍展示空态文案', async () => {
    // 只有非 tools 类目：目录工具池为空（画廊池非空，证明空态来自工具池而非示例为空）。
    // 交互工具恒在列——目录池空不再等于工具池空；收藏过滤（无收藏）连交互工具一并滤掉，
    // 工具池此时才真正为空。
    examples.value = [makeExample({ id: 't', category: 'topics' })]
    const w = mount(ToolboxView)
    expect(w.text()).not.toContain('没有匹配的工具')
    favOnly.value = true
    await nextTick()
    expect(w.text()).toContain('没有匹配的工具')
  })

  it('工具池为空时页头仍然可见——它是退出筛选的唯一入口', () => {
    // 交互工具恒在列：工具池为空只能由过滤造成（此处收藏过滤且无收藏）
    examples.value = [makeExample({ id: 't', category: 'topics' })]
    favOnly.value = true
    const w = mount(ToolboxView)

    expect(w.text()).toContain('没有匹配的工具')
    // 回归：空态曾整块替换页头，用户因此无法清空搜索词或关掉「只看收藏」，被永久困住。
    // favOnly 预置为 true（空态的成因），星标处于激活态，aria-label 是「显示全部工具」——
    // 它恰是逃生入口本身。
    expect(w.find('input[placeholder="搜索工具…"]').exists()).toBe(true)
    expect(w.find('select').exists()).toBe(true)
    expect(w.findAll('button').some((b) => b.attributes('aria-label') === '显示全部工具')).toBe(true)
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
    // 工具数 = 目录池 9 + 交互工具 1（toolsTotal 口径）；可静态运行率分母只数目录池
    // （交互工具无 .py 文件不进分母，9/9 = 100%，不被交互工具稀释）。
    // 项目数 = 2 个 source_dir 项目；「交互工具」组有意排除——它是应用内页面门面，不是工具项目。
    expect(w.text()).toContain('119 个工具 · 2 个工具项目 · 100% 可静态运行')
  })

  it('按 source_dir 分组：交互工具组恒置顶，内置项目用中文区名、按声明序排列，无 source_dir 归入独立工具', () => {
    examples.value = toolFixtures()
    const w = mount(ToolboxView)
    expect(w.findAll('section.mb-9 h2').map((h) => h.text())).toEqual([
      '交互工具',
      'Python 黑魔法',
      '实用爬虫合集',
      '独立工具'
    ])
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

  it('点击普通工具卡片经 openDetail 打开详情；点击交互工具卡片走 openInteractive（selectedId 置交互 id）', async () => {
    examples.value = [makeExample({ id: 'only', name: 'only_tool.py', category: 'tools' })]
    const w = mount(ToolboxView)
    // 交互组置顶后第一张卡是交互工具，普通工具卡按 aria-label 精确命中
    await w.find('[aria-label="only tool（详情）"]').trigger('click')
    expect(selectedId.value).toBe('only')

    // 交互工具不经 openDetail（无详情页），直接置交互 id，App.vue 按前缀渲染专属页
    // （aria-label 后缀随卡片形态切换：普通卡=详情，interactive 卡=打开）
    // 交互组按质量分并列排序，W6 后 date-calculator 不再保证落在前 6 张预览窗内——
    // 先点「展开全部」再选（顺带覆盖展开路径）
    const expandBtn = w.findAll('button').find((b) => b.text().includes('展开全部'))
    if (expandBtn) await expandBtn.trigger('click')
    await w.find('[aria-label="日期计算器（打开）"]').trigger('click')
    expect(selectedId.value).toBe('interactive:date-calculator')
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
    expect(
      w
        .findAll('button')
        .find((b) => b.attributes('title') === '显示全部工具')!
        .attributes('aria-pressed')
    ).toBe('true')
  })
})

// ---------------------------------------------------------------------------
// 画廊工具栏筛选下拉（原独立筛选栏 FilterSidebar 已退役，筛选收成工具栏下拉）
// ---------------------------------------------------------------------------
describe('画廊工具栏筛选下拉', () => {
  // 两条画廊示例：a 命中 turtle 主题 + runnable；b 命中 games 主题 + missing_deps。
  function facetFixtures(): VExample[] {
    return [
      makeExample({
        id: 'a',
        name: 'turtle_draw.py',
        code: 'import turtle\n',
        tags: ['基础'],
        quality_score: 90,
        run_status: 'runnable',
        theme_key: 'turtle'
      }),
      makeExample({
        id: 'b',
        name: 'beta.py',
        code: 'import pygame\n',
        tags: ['游戏'],
        quality_score: 60,
        run_status: 'missing_deps',
        theme_key: 'games'
      })
    ]
  }

  // BaseSelectMenu：触发器按钮 + 点开后的菜单项（无 Portal，wrapper 内查询）
  const trigger = (w: VueWrapper, testid: string) => w.get(`[data-testid="${testid}"]`)
  async function openMenu(w: VueWrapper, testid: string) {
    await trigger(w, testid).trigger('click')
    await flushPromises()
    return w.findAll('[role="menuitemradio"]')
  }
  async function pick(w: VueWrapper, testid: string, label: string) {
    // 菜单可能已被 openMenu 打开（再点触发器会把它关掉）：已开则直接复用
    let items = w.findAll('[role="menuitemradio"]')
    if (items.length === 0) items = await openMenu(w, testid)
    const item = items.find((i) => i.text().replace(/\s+/g, ' ').trim().startsWith(label))
    expect(item, `菜单项 ${label} 不存在`).toBeTruthy()
    await item!.trigger('click')
    await flushPromises()
  }

  it('渲染筛选维度下拉 + 排序 + 标签多选，均带标题（可运行性已退役：负面状态由卡片徽章表达）', () => {
    const w = mount(BrowseToolbar)
    expect(trigger(w, 'filter-theme').attributes('title')).toBe('主题')
    expect(w.find('[data-testid="filter-runnable"]').exists()).toBe(false)
    expect(w.find('[data-testid="filter-quality"]').exists()).toBe(false)
    expect(w.find('[data-testid="filter-run-status"]').exists()).toBe(false)
    expect(trigger(w, 'filter-sort').attributes('title')).toBe('排序')
    expect(w.find('[data-testid="tag-filter-select"]').exists()).toBe(true)
  })

  it('主题下拉：全部主题 + 5 主题，且每档带 facet 计数', async () => {
    examples.value = facetFixtures()
    const w = mount(BrowseToolbar)
    const opts = await openMenu(w, 'filter-theme')
    expect(opts).toHaveLength(6)
    expect(opts[0].text().trim()).toBe('全部主题')
    // turtle 命中 a → 计数 1
    expect(opts.find((o) => o.text().trim().startsWith('Turtle 绘图'))!.text()).toContain('(1)')
  })

  it('选择主题：写回 activeTheme、持久化 viewPrefs、结果随之收敛', async () => {
    examples.value = facetFixtures()
    const w = mount(BrowseToolbar)
    await pick(w, 'filter-theme', 'Turtle 绘图')
    expect(activeTheme.value).toBe('turtle')
    expect(vi.mocked(window.sidecar.store.set)).toHaveBeenCalledWith(
      'viewPrefs',
      expect.objectContaining({ activeTheme: 'turtle' })
    )
  })

  it('标签多选下拉：勾选写入 activeTags（checkbox），再取消移除', async () => {
    examples.value = facetFixtures()
    const w = mount(BrowseToolbar)
    await w.get('[data-testid="tag-filter-select"]').trigger('click')
    const menu = w.get('[data-testid="tag-filter-menu"]')
    const base = menu.findAll('label').find((l) => l.attributes('title') === '基础')!

    await base.get('input[type="checkbox"]').trigger('change')
    expect(activeTags.value.has('基础')).toBe(true)
    await base.get('input[type="checkbox"]').trigger('change')
    expect(activeTags.value.has('基础')).toBe(false)
  })

  it('收藏开关：切换 favOnly 并显示收藏计数（不塞进下拉）', async () => {
    favorites.value = new Set(['a', 'b'])
    const w = mount(BrowseToolbar)
    const toggle = w.get('[data-testid="filter-fav-toggle"]')
    expect(toggle.text()).toContain('2')

    await toggle.trigger('click')
    expect(favOnly.value).toBe(true)
    expect(toggle.attributes('aria-pressed')).toBe('true')
  })

  it('筛选可与侧栏分区范围叠加（sections 与 theme 互不吞并）', () => {
    examples.value = facetFixtures()
    activeTheme.value = 'turtle'
    activeSectionKey.value = 'tag:basics'
    const w = mount(BrowseToolbar)
    // 范围语义由页头标题表达（GalleryHeader），工具栏只管筛选维度
    // 主题下拉仍保留选中值——两维叠加，未互相清空
    expect(trigger(w, 'filter-theme').text()).toContain('Turtle 绘图')
    expect(activeSectionKey.value).toBe('tag:basics')
  })

  it('结果条芯片可逐个移除：主题芯片复位 activeTheme，不动分区范围', async () => {
    activeTheme.value = 'turtle'
    activeSectionKey.value = 'tag:basics'
    const w = mount(BrowseToolbar)
    await w.get('button[title="移除筛选：Turtle 绘图"]').trigger('click')
    expect(activeTheme.value).toBe('all')
    expect(activeSectionKey.value).toBe('tag:basics')
  })
})
