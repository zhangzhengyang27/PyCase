// cards 层组件测试：依赖 store 单例的展示/交互组件（卡片、列表行、结果条、总览、
// 参数表单、历史、输出面板）。
//
// 与 base 层的关键差别：这一层直接 import store 的模块级 ref 并读写它，所以每个用例
// 前必须把 store 恢复成干净态——上一个用例残留的筛选/收藏/运行态会静默改变下一个
// 用例的输入，是组件测试里最典型的假绿来源。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import ExampleCard from '../ExampleCard.vue'
import ExampleListItem from '../ExampleListItem.vue'
import BrowseToolbar from '../BrowseToolbar.vue'
import GalleryHeader from '../GalleryHeader.vue'
import ArgsForm from '../ArgsForm.vue'
import HistoryPanel from '../HistoryPanel.vue'
import OutputPanel from '../OutputPanel.vue'

import { runStatusHint } from '../../src/utils'
import type { RunHistoryEntry } from '../../src/types'
import {
  activeSectionKey,
  activeTheme,
  examples,
  favOnly,
  sortBy,
  viewMode,
  type VExample
} from '../../src/store/catalog'
import {
  argsError,
  argsLoading,
  clearSurface,
  currentArgs,
  isDirty,
  isRunning,
  pendingBackfillTokens,
  selectedId,
  surfaceState
} from '../../src/store/detail'
import { getTestApi } from '../../src/store/index'
import { favorites, runHistory } from '../../src/store/prefs'

// getTestApi() 的声明返回 Record<string, unknown>（它是给 E2E 探针用的宽类型），
// 这里只挑本文件用到的几个钩子做窄化，避免把 unknown 散落到每处断言。
const testApi = getTestApi() as unknown as {
  resetViewFilters: () => void
  collectArgs: () => string[]
  setArgValue: (idx: number, v: string) => void
}

// 卡片/列表行/总览共用的示例工厂：默认值刻意选「无主题、无标签、可运行」，
// 让每个用例只通过 overrides 声明它真正关心的那一维。
function makeExample(overrides: Partial<VExample> = {}): VExample {
  return {
    id: 'ex-1',
    name: 'demo_script.py',
    category: 'topics',
    path: '/examples/demo_script.py',
    code: '',
    description: '示例描述',
    tags: [],
    quality_score: 85,
    run_status: 'runnable',
    // 派生事实（v2）：主题判定读 theme_key 而非 code；默认无主题，用例按需覆盖
    theme_key: null,
    import_tags: [],
    ...overrides
  }
}

function makeEntry(overrides: Partial<RunHistoryEntry> = {}): RunHistoryEntry {
  return {
    ts: '2026-01-01T10:00:00.000Z',
    id: 'e1',
    name: 'demo.py',
    args: [],
    duration_ms: 500,
    exit_code: 0,
    ok: true,
    ...overrides
  }
}

// @vue/test-utils 默认不会卸载已挂载的组件，跨用例残留的实例会继续持有 store 的
// watcher，而 ArgsForm 的参数回填令牌是「模块级 ref + 一次性消费」——残留实例会抢先
// 把令牌吃掉，导致本用例真正挂载的实例拿不到回填值。
// 卸载已由 vitest.setup.ts 统一开启（enableAutoUnmount），此处不再重复注册。

beforeEach(() => {
  testApi.resetViewFilters()
  examples.value = []
  favorites.value = new Set<string>()
  runHistory.value = []
  selectedId.value = null
  isDirty.value = false
  currentArgs.value = []
  argsLoading.value = false
  pendingBackfillTokens.value = null
  isRunning.value = false
  sortBy.value = 'quality_desc'
  viewMode.value = 'grid'
  clearSurface('detail')
  clearSurface('runner')

  // restoreMocks 会在每个用例前把 vitest.setup.ts 里的 vi.fn 桩重置掉，
  // 这里显式重建本文件依赖的返回值，保证断言不受「桩被重置成 undefined」影响。
  vi.mocked(window.sidecar.parseArgs).mockResolvedValue({ args: [], count: 0 })
  vi.mocked(window.sidecar.runExample).mockResolvedValue({ run_id: 'test-run' })
  vi.mocked(window.sidecar.listAssets).mockResolvedValue({ assets: [] })
  vi.mocked(window.sidecar.store.set).mockResolvedValue({ ok: true })
})

afterEach(() => {
  document.body.innerHTML = ''
})

// ---------------------------------------------------------------------------
// ExampleCard
// ---------------------------------------------------------------------------
describe('ExampleCard', () => {
  it('标题优先取 ex.title，否则由 name 去扩展名并把 -/_ 换成空格', () => {
    const fromName = mount(ExampleCard, { props: { ex: makeExample({ name: 'my_cool-tool.py' }) } })
    // aria-label 复用同一个 computed，改标题逻辑时两处会一起暴露
    expect(fromName.get('[role="button"]').attributes('aria-label')).toBe('my cool tool（详情）')
    expect(fromName.text()).toContain('my cool tool')

    const fromTitle = mount(ExampleCard, {
      props: { ex: makeExample({ name: 'ignored.py', title: '自定义标题.py' }) }
    })
    expect(fromTitle.get('[role="button"]').attributes('aria-label')).toBe('自定义标题（详情）')
  })

  it('描述为空时回退「暂无描述」', () => {
    expect(mount(ExampleCard, { props: { ex: makeExample({ description: '' }) } }).text()).toContain('暂无描述')
    expect(mount(ExampleCard, { props: { ex: makeExample({ description: '有描述' }) } }).text()).toContain('有描述')
  })

  it('selected 才加选中描边类', () => {
    expect(
      mount(ExampleCard, { props: { ex: makeExample(), selected: true } })
        .get('[role="button"]')
        .classes()
    ).toContain('card-sel')
    expect(
      mount(ExampleCard, { props: { ex: makeExample() } })
        .get('[role="button"]')
        .classes()
    ).not.toContain('card-sel')
  })

  it('入场 stagger：前 8 项按序号 ×20ms 延迟，第 8 项起与未传时都不延迟', () => {
    const styleOf = (enterIndex?: number): string =>
      mount(ExampleCard, { props: { ex: makeExample(), enterIndex } })
        .get('[role="button"]')
        .attributes('style') || ''

    expect(styleOf(0)).toContain('animation-delay: 0ms')
    expect(styleOf(3)).toContain('animation-delay: 60ms')
    // 第 8 项起归零：长列表末尾不该再叠出夸张的等待
    expect(styleOf(8)).toContain('animation-delay: 0ms')
    expect(styleOf(undefined)).toContain('animation-delay: 0ms')
  })

  it('点击卡片 emit open；收藏/运行按钮的 .stop 阻止冒泡出 open', async () => {
    const w = mount(ExampleCard, { props: { ex: makeExample() } })

    await w.get('[role="button"]').trigger('click')
    expect(w.emitted('open')).toHaveLength(1)

    await w.get('button[title="收藏"]').trigger('click')
    expect(w.emitted('fav')).toHaveLength(1)

    await w.get('button[title="运行"]').trigger('click')
    expect(w.emitted('run')).toHaveLength(1)

    // 两次按钮点击都没有把 open 再冒泡一次
    expect(w.emitted('open')).toHaveLength(1)
  })

  it('Enter / Space 键盘激活等价于点击（role=button 且可 Tab 到达）', async () => {
    const w = mount(ExampleCard, { props: { ex: makeExample() } })
    const card = w.get('[role="button"]')
    expect(card.attributes('tabindex')).toBe('0')

    await card.trigger('keydown', { key: 'Enter' })
    await card.trigger('keydown', { key: ' ' })
    expect(w.emitted('open')).toHaveLength(2)
  })

  it('焦点落在内嵌按钮上：Enter/Space 只激活按钮，不再冒泡出 open（双触发回归）', async () => {
    const w = mount(ExampleCard, { props: { ex: makeExample() } })

    // 真实键盘路径：Tab 进入卡片后焦点停在 ★ / 运行按钮上，keydown 自按钮冒泡到容器——
    // 修复前容器与按钮同时响应（按 Enter = 收藏 + 打开详情）
    await w.get('button[title="收藏"]').trigger('keydown', { key: 'Enter' })
    await w.get('button[title="收藏"]').trigger('keydown', { key: ' ' })
    expect(w.emitted('open')).toBeUndefined()

    // 容器自身的键盘路径不受影响
    await w.get('[role="button"]').trigger('keydown', { key: 'Enter' })
    expect(w.emitted('open')).toHaveLength(1)
  })

  it('收藏态切换星标配色、填充与 aria-label', () => {
    const on = mount(ExampleCard, { props: { ex: makeExample({ name: 'demo.py' }), faved: true } })
    const onBtn = on.get('button[title="取消收藏"]')
    expect(onBtn.attributes('aria-label')).toBe('取消收藏 demo')
    expect(onBtn.find('svg').classes()).toContain('fill-current')

    const off = mount(ExampleCard, { props: { ex: makeExample({ name: 'demo.py' }) } })
    const offBtn = off.get('button[title="收藏"]')
    expect(offBtn.attributes('aria-label')).toBe('收藏 demo')
    expect(offBtn.classes()).toContain('text-ink-faint')
    expect(offBtn.find('svg').classes()).not.toContain('fill-current')
  })

  it('质量分：缺失按 0 显示，60 分以下才切警示色（v2 无底色徽章）', () => {
    const badge = (score?: number) =>
      mount(ExampleCard, { props: { ex: makeExample({ quality_score: score }) } }).get(
        '[title="六维质量评分（0-100）"]'
      )

    expect(badge(85).text()).toBe('85')
    expect(badge(85).classes()).toContain('text-ink-mute')
    expect(badge(60).classes()).toContain('text-ink-mute')
    expect(badge(59).classes()).toContain('text-warn')
    // undefined 不渲染空白，而是回退 0
    expect(badge(undefined).text()).toBe('0')
  })

  it('主标签位只展示第一个标签；无标签时不渲染标签位', () => {
    const w = mount(ExampleCard, { props: { ex: makeExample({ tags: ['pandas', 'numpy'] }) } })
    expect(w.find('span[title="pandas"]').text()).toBe('pandas')
    expect(w.find('span[title="numpy"]').exists()).toBe(false)

    const none = mount(ExampleCard, { props: { ex: makeExample({ tags: [] }) } })
    expect(none.findAll('span').some((s) => s.attributes('title') === 'pandas')).toBe(false)
  })

  it('risk_high 渲染高危徽章并带审阅提示，否则不渲染', () => {
    const risky = mount(ExampleCard, { props: { ex: makeExample({ risk_high: true }) } })
    const badge = risky.get('[title^="含高危操作"]')
    expect(badge.text()).toContain('高危')
    // v2：状态 = 圆点 + 文字，高危用红字，底色徽章退役
    expect(badge.classes()).toContain('text-danger')
    expect(badge.find('.stat-dot').classes()).toContain('bg-danger')

    expect(
      mount(ExampleCard, { props: { ex: makeExample() } })
        .find('[title^="含高危操作"]')
        .exists()
    ).toBe(false)
  })

  it('可运行性状态只显示负面：缺依赖出圆点 + 中性文字，runnable/risky 让位给正向与高危展示', () => {
    const w = mount(ExampleCard, { props: { ex: makeExample({ run_status: 'missing_deps' }) } })
    const badge = w.findAll('span').find((s) => s.text() === '缺依赖')!
    expect(badge.classes()).toContain('text-ink-mute')
    expect(badge.find('.stat-dot').classes()).toContain('bg-warn')
    expect(badge.attributes('title')).toBe(runStatusHint('missing_deps'))

    // runnable 是正向状态、risky 由高危徽章承担：两者都不该再出一个徽章
    expect(mount(ExampleCard, { props: { ex: makeExample({ run_status: 'runnable' }) } }).text()).not.toContain(
      '可运行'
    )
    expect(mount(ExampleCard, { props: { ex: makeExample({ run_status: 'risky' }) } }).text()).not.toContain('高危')
  })

  it('图标 chip：命中分区与未命中都出 Lucide 图标（v2 无 emoji、无色相）', () => {
    const themed = mount(ExampleCard, {
      props: { ex: makeExample({ name: 'basic-demo', tags: ['python-basics'] }) }
    })
    const themedChip = themed.get('.chip-ic')
    expect(themedChip.find('svg').exists()).toBe(true)
    expect(themedChip.text()).toBe('')

    const fallback = mount(ExampleCard, { props: { ex: makeExample({ category: 'unknown', tags: [] }) } })
    expect(fallback.get('.chip-ic').find('svg').exists()).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// ExampleListItem
// ---------------------------------------------------------------------------
describe('ExampleListItem', () => {
  it('名称列 title 属性复用计算标题，描述为空回退「暂无描述」', () => {
    const w = mount(ExampleListItem, { props: { ex: makeExample({ name: 'my_tool.py', description: '' }) } })
    expect(w.get('span[title="my tool"]').text()).toBe('my tool')
    expect(w.text()).toContain('暂无描述')

    expect(mount(ExampleListItem, { props: { ex: makeExample({ description: '有描述' }) } }).text()).toContain('有描述')
  })

  it('质量分只在低分（<80）出现，undefined 按 0 处理', () => {
    const low = mount(ExampleListItem, { props: { ex: makeExample({ quality_score: 59 }) } })
    expect(low.get('[title="六维质量评分（0-100）"]').text()).toBe('59')
    expect(low.get('[title="六维质量评分（0-100）"]').classes()).toContain('text-warn')

    // 80 分是边界：不打扰扫读，不渲染徽章
    expect(
      mount(ExampleListItem, { props: { ex: makeExample({ quality_score: 80 }) } })
        .find('[title="六维质量评分（0-100）"]')
        .exists()
    ).toBe(false)

    expect(
      mount(ExampleListItem, { props: { ex: makeExample({ quality_score: undefined }) } })
        .get('[title="六维质量评分（0-100）"]')
        .text()
    ).toBe('0')
  })

  it('标签最多展示 2 个', () => {
    const w = mount(ExampleListItem, { props: { ex: makeExample({ tags: ['pandas', 'numpy', 'extra'] }) } })
    const texts = w.findAll('span').map((s) => s.text())
    expect(texts).toContain('pandas')
    expect(texts).toContain('numpy')
    expect(texts).not.toContain('extra')
  })

  it('收藏态：星标填充为警告色，aria-label 随状态切换', () => {
    const on = mount(ExampleListItem, { props: { ex: makeExample({ name: 'demo.py' }), faved: true } })
    const onBtn = on.get('button[title="取消收藏"]')
    expect(onBtn.attributes('aria-label')).toBe('取消收藏 demo')
    expect(onBtn.find('svg').classes()).toContain('text-warn')
    expect(onBtn.find('svg').classes()).toContain('fill-current')

    const off = mount(ExampleListItem, { props: { ex: makeExample({ name: 'demo.py' }) } })
    const offBtn = off.get('button[title="收藏"]')
    expect(offBtn.attributes('aria-label')).toBe('收藏 demo')
    expect(offBtn.find('svg').classes()).not.toContain('text-warn')
  })

  it('行点击 / Enter / Space 都 emit open；行内按钮只 emit 各自事件', async () => {
    const w = mount(ExampleListItem, { props: { ex: makeExample() } })
    const row = w.get('[role="button"]')
    expect(row.attributes('tabindex')).toBe('0')

    await row.trigger('click')
    await row.trigger('keydown', { key: 'Enter' })
    await row.trigger('keydown', { key: ' ' })
    expect(w.emitted('open')).toHaveLength(3)

    await w.get('button[title="收藏"]').trigger('click')
    await w.get('button[title="运行"]').trigger('click')
    expect(w.emitted('fav')).toHaveLength(1)
    expect(w.emitted('run')).toHaveLength(1)
    // .stop 生效：按钮点击没有再冒泡出 open
    expect(w.emitted('open')).toHaveLength(3)
  })

  it('焦点落在内嵌按钮上：Enter/Space 只激活按钮，不再冒泡出 open（双触发回归）', async () => {
    const w = mount(ExampleListItem, { props: { ex: makeExample() } })

    await w.get('button[title="收藏"]').trigger('keydown', { key: 'Enter' })
    await w.get('button[title="运行"]').trigger('keydown', { key: ' ' })
    expect(w.emitted('open')).toBeUndefined()

    // 容器自身的键盘路径不受影响
    await w.get('[role="button"]').trigger('keydown', { key: 'Enter' })
    expect(w.emitted('open')).toHaveLength(1)
  })

  it('入场 stagger 与卡片同口径（前 8 项 ×20ms）', () => {
    const styleOf = (enterIndex?: number): string =>
      mount(ExampleListItem, { props: { ex: makeExample(), enterIndex } })
        .get('[role="button"]')
        .attributes('style') || ''
    expect(styleOf(2)).toContain('animation-delay: 40ms')
    expect(styleOf(8)).toContain('animation-delay: 0ms')
  })

  it('高危与负面可运行性徽章口径同卡片（risky 不额外出徽章）', () => {
    const risky = mount(ExampleListItem, {
      props: { ex: makeExample({ risk_high: true, run_status: 'risky' }) }
    })
    expect(risky.get('[title^="含高危操作"]').text()).toContain('高危')
    // risky 已由高危徽章承担，不应再渲染一枚「高危」状态徽章
    expect(risky.findAll('span').filter((s) => s.text() === '高危')).toHaveLength(1)

    const broken = mount(ExampleListItem, { props: { ex: makeExample({ run_status: 'broken' }) } })
    const badge = broken.findAll('span').find((s) => s.text() === '语法损坏')!
    expect(badge.attributes('title')).toBe(runStatusHint('broken'))

    expect(mount(ExampleListItem, { props: { ex: makeExample({ run_status: 'runnable' }) } }).text()).not.toContain(
      '可运行'
    )
  })
})

// ---------------------------------------------------------------------------
// BrowseToolbar
// ---------------------------------------------------------------------------
describe('BrowseToolbar', () => {
  // 范围标题 span 是唯一「有 title 属性且带 font-medium 的 span」，
  // 用类名数组精确匹配（不写 CSS 转义）比按结构取 nth-child 稳。
  function scopeTitle(): string {
    const w = mount(BrowseToolbar)
    const el = w
      .findAll('span')
      .find((s) => s.classes().includes('font-medium') && s.attributes('title') !== undefined)!
    return el.text()
  }

  it('范围标题优先级：分区 > 主题 > 全部示例', () => {
    expect(scopeTitle()).toBe('全部示例')

    activeTheme.value = 'turtle'
    expect(scopeTitle()).toBe('Turtle 绘图')

    // 分区（侧栏二级菜单）标题优先于主题 facet
    activeTheme.value = 'all'
    activeSectionKey.value = 'tag:basics'
    expect(scopeTitle()).toBe('语言基础')

    activeTheme.value = 'viz'
    activeSectionKey.value = 'projects'
    expect(scopeTitle()).toBe('综合项目')

    // 分区 key 认不出来时回退到主题 / 全部示例，不露空白标题
    activeSectionKey.value = 'no-such-key'
    activeTheme.value = 'all'
    expect(scopeTitle()).toBe('全部示例')
  })

  it('结果计数取 filtered.length（tools 不进画廊池）并带 aria-live', () => {
    examples.value = [makeExample({ id: 'a' }), makeExample({ id: 'b', category: 'tools' })]
    const w = mount(BrowseToolbar)
    const count = w.get('[aria-live="polite"]')
    expect(count.text()).toBe('1 个结果')
  })

  it('无筛选时渲染占位区，不渲染芯片区与「清空」', () => {
    const w = mount(BrowseToolbar)
    expect(w.find('.overflow-x-auto').exists()).toBe(false)
    expect(w.text()).not.toContain('清空')
  })

  it('筛选芯片：按维度逐个移除，互不牵连', async () => {
    favOnly.value = true
    activeTheme.value = 'turtle'
    const w = mount(BrowseToolbar)
    expect(w.text()).toContain('我的收藏')
    expect(w.text()).toContain('Turtle 绘图')

    await w.get('button[title="移除筛选：我的收藏"]').trigger('click')
    expect(favOnly.value).toBe(false)
    // 只复位被移除的那一维
    expect(activeTheme.value).toBe('turtle')

    await w.get('button[title="移除筛选：Turtle 绘图"]').trigger('click')
    expect(activeTheme.value).toBe('all')
  })

  it('「清空」复位全部筛选（含收藏开关）', async () => {
    favOnly.value = true
    activeTheme.value = 'turtle'
    const w = mount(BrowseToolbar)

    const clear = w.findAll('button').find((b) => b.text() === '清空')!
    await clear.trigger('click')
    expect(favOnly.value).toBe(false)
    expect(activeTheme.value).toBe('all')
    expect(w.find('.overflow-x-auto').exists()).toBe(false)
  })

  it('排序下拉双向绑定 sortBy（BaseSelectMenu：点开菜单选项）', async () => {
    const w = mount(BrowseToolbar)
    const trigger = w.get('[data-testid="filter-sort"]')
    expect(trigger.attributes('title')).toBe('排序')
    expect(trigger.text()).toContain('质量分优先')

    await trigger.trigger('click')
    await flushPromises()
    // 无 Portal：菜单渲染在组件树内（游离子树），用 wrapper 查询而非 document.body
    const items = w.findAll('[role="menuitemradio"]')
    expect(items.map((i) => i.text().trim())).toContain('按名称')
    const item = items.find((i) => i.text().trim() === '按名称')!
    await item.trigger('click')
    await flushPromises()
    expect(sortBy.value).toBe('name')
  })

  it('密度切换写入 viewMode、持久化 viewPrefs，并用 aria-pressed 反映当前态', async () => {
    const w = mount(BrowseToolbar)
    // v2：分段控件走平台语义（.seg + aria-pressed），选中态由 CSS 按 data-platform 决定
    expect(w.find('.seg').exists()).toBe(true)
    expect(w.get('button[aria-label="网格视图"]').attributes('aria-pressed')).toBe('true')
    expect(w.get('button[aria-label="列表视图"]').attributes('aria-pressed')).toBe('false')

    await w.get('button[aria-label="列表视图"]').trigger('click')
    expect(viewMode.value).toBe('list')
    expect(w.get('button[aria-label="列表视图"]').attributes('aria-pressed')).toBe('true')
    expect(w.get('button[aria-label="网格视图"]').attributes('aria-pressed')).toBe('false')
    expect(vi.mocked(window.sidecar.store.set)).toHaveBeenCalledWith(
      'viewPrefs',
      expect.objectContaining({ viewMode: 'list' })
    )
  })

  it('面包屑「示例库」把分区范围归零（回到全部示例）', async () => {
    activeSectionKey.value = 'projects'
    const w = mount(BrowseToolbar)
    await w.get('button[title="全部示例"]').trigger('click')
    expect(activeSectionKey.value).toBeNull()
  })

  it('筛选维度收成工具栏下拉：5 个维度 + 排序（旧「筛选」按钮与浮层已退役）', () => {
    const w = mount(BrowseToolbar)
    expect(w.find('[data-testid="gallery-filter-toggle"]').exists()).toBe(false)
    expect(w.find('[data-testid="filter-theme"]').exists()).toBe(true)
    expect(w.find('[data-testid="filter-runnable"]').exists()).toBe(true)
    expect(w.find('[data-testid="filter-quality"]').exists()).toBe(true)
    expect(w.find('[data-testid="filter-run-status"]').exists()).toBe(true)
    expect(w.find('[data-testid="filter-sort"]').exists()).toBe(true)
    expect(w.find('[data-testid="tag-filter-select"]').exists()).toBe(true)
    expect(w.find('[data-testid="filter-fav-toggle"]').exists()).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// GalleryHeader
// ---------------------------------------------------------------------------
// 总览落地页退役后，头区抽为独立组件：统计 chip + 浏览全部 / 我的收藏。
// 分区导航改由侧栏二级菜单承担（见 App.vue），此处只锁定页头的统计口径与入口行为。
describe('GalleryHeader', () => {
  it('页头统计与卡片同口径：示例数 / 主题数 / 可运行百分比 / 收藏数', () => {
    examples.value = [
      makeExample({ id: 'a', run_status: 'runnable' }),
      makeExample({ id: 'b', run_status: 'missing_deps' })
    ]
    favorites.value = new Set(['a'])
    const w = mount(GalleryHeader)

    const chips = w.findAll('.stat-chip')
    expect(chips.map((c) => c.text())).toEqual(['2 个示例', '5 大主题', '50% 可运行', '1 收藏'])
    // 可运行百分比用「强调」样式单独着色
    expect(chips[2].classes()).toContain('stat-chip-ok')
  })

  it('空库时可运行百分比回退 0，不出现 NaN', () => {
    const w = mount(GalleryHeader)
    expect(w.findAll('.stat-chip')[2].text()).toBe('0% 可运行')
  })

  it('横向卡片带已退役：页头不再渲染卡片与「还有 N 个」下钻', () => {
    examples.value = Array.from({ length: 7 }, (_, i) =>
      makeExample({ id: `t${i}`, name: `turtle-demo-${i}.py`, quality_score: 90 - i, theme_key: 'turtle' })
    )
    const w = mount(GalleryHeader)
    // 卡片统一由右侧网格渲染，页头只剩统计 chip 与两个入口按钮
    expect(w.findAllComponents(ExampleCard)).toHaveLength(0)
    expect(w.findAll('button').every((b) => !b.text().includes('还有'))).toBe(true)
  })

  it('收藏 chip 数随 favorites 变化即时更新', async () => {
    examples.value = [makeExample({ id: 'a' })]
    const w = mount(GalleryHeader)
    expect(w.findAll('.stat-chip')[3].text()).toBe('0 收藏')

    favorites.value = new Set(['a'])
    await w.vm.$nextTick()
    expect(w.findAll('.stat-chip')[3].text()).toBe('1 收藏')
  })

  it('页头入口：浏览全部范围归零；我的收藏额外打开 favOnly（并清掉分区范围）', async () => {
    activeSectionKey.value = 'projects'
    const w = mount(GalleryHeader)

    await w
      .findAll('button')
      .find((b) => b.text() === '浏览全部')!
      .trigger('click')
    expect(activeSectionKey.value).toBeNull()

    activeSectionKey.value = 'projects'
    await w
      .findAll('button')
      .find((b) => b.text() === '我的收藏')!
      .trigger('click')
    expect(favOnly.value).toBe(true)
    expect(activeSectionKey.value).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// ArgsForm
// ---------------------------------------------------------------------------
describe('ArgsForm', () => {
  it('解析中只显示加载文案，不渲染任何字段', () => {
    argsLoading.value = true
    currentArgs.value = [{ name: '--a', flags: ['--a'], dest: 'a', type: 'str' }]
    const w = mount(ArgsForm)

    expect(w.text()).toBe('解析参数中…')
    expect(w.find('input').exists()).toBe(false)
  })

  it('解析失败时显示错误与「重试解析」，不再静默成"没有参数"（A6 失败恢复）', async () => {
    const ex = { id: 't1', name: 'alpha.py', category: 'topics', path: '/tmp/alpha.py' }
    examples.value = [ex as never]
    selectedId.value = 't1'
    argsError.value = '[parseArgs] 解析器崩了（错误码 -32602）'
    const w = mount(ArgsForm)

    const box = w.get('[data-testid="args-error"]')
    expect(box.text()).toContain('参数解析失败')
    expect(box.text()).toContain('-32602')

    vi.mocked(window.sidecar.parseArgs).mockResolvedValue({ args: [], count: 0 })
    await box.get('button').trigger('click')
    await flushPromises()
    expect(window.sidecar.parseArgs).toHaveBeenCalledWith('t1')
    expect(argsError.value).toBe('')
  })

  it('无参数时不渲染任何内容', () => {
    const w = mount(ArgsForm)
    expect(w.find('input').exists()).toBe(false)
    expect(w.find('select').exists()).toBe(false)
    expect(w.text()).toBe('')
  })

  it('文本 / 数字字段：类型、步长、placeholder 与收集顺序', async () => {
    currentArgs.value = [
      { name: '--name', flags: ['--name'], dest: 'name', type: 'str' },
      { name: '--count', flags: ['--count'], dest: 'count', type: 'int' },
      { name: '--ratio', flags: ['--ratio'], dest: 'ratio', type: 'float' },
      { name: 'file', flags: [], dest: 'file', type: 'str', is_positional: true }
    ]
    const w = mount(ArgsForm)
    const inputs = w.findAll('input')
    expect(inputs).toHaveLength(4)

    expect(inputs[0].attributes('type')).toBe('text')
    expect(inputs[0].attributes('placeholder')).toBe('name')
    expect(inputs[1].attributes('type')).toBe('number')
    expect(inputs[1].attributes('step')).toBe('1')
    expect(inputs[2].attributes('type')).toBe('number')
    expect(inputs[2].attributes('step')).toBe('any')
    expect(inputs[0].attributes('spellcheck')).toBe('false')

    return (async () => {
      await inputs[0].setValue('alice')
      await inputs[1].setValue('3')
      await inputs[2].setValue('1.5')
      await inputs[3].setValue('data.txt')
      // 非位置参数展开成 flag + value；位置参数只推值本身
      expect(testApi.collectArgs()).toEqual(['--name', 'alice', '--count', '3', '--ratio', '1.5', 'data.txt'])
    })()
  })

  it('choices 渲染成下拉，默认值回填，收集时按选中项展开', async () => {
    currentArgs.value = [
      { name: '--mode', flags: ['--mode'], dest: 'mode', type: 'str', choices: ['fast', 'slow'], default: 'slow' }
    ]
    const w = mount(ArgsForm)
    const select = w.get('select')
    expect(select.findAll('option').map((o) => o.text())).toEqual(['fast', 'slow'])
    expect((select.element as HTMLSelectElement).value).toBe('slow')

    await select.setValue('fast')
    expect(testApi.collectArgs()).toEqual(['--mode', 'fast'])
  })

  it('布尔开关：store_true 勾选才推 flag，store_false 取消勾选才推 flag，缺 flags 回退 --dest', async () => {
    currentArgs.value = [
      { name: '--verbose', flags: ['--verbose'], dest: 'verbose', type: 'bool', action: 'store_true' },
      { name: '--no-cache', flags: ['--no-cache'], dest: 'no_cache', type: 'bool', action: 'store_false' },
      { name: '--quiet', flags: [], dest: 'quiet', type: 'bool', action: 'store_true' }
    ]
    const w = mount(ArgsForm)
    const boxes = w.findAll('input[type="checkbox"]')
    expect(boxes).toHaveLength(3)

    expect((boxes[0].element as HTMLInputElement).checked).toBe(false)
    // store_false 的语义是「默认开启」，未传 default 时初始即勾选
    expect((boxes[1].element as HTMLInputElement).checked).toBe(true)
    expect(testApi.collectArgs()).toEqual([])

    await boxes[0].setValue(true)
    await boxes[1].setValue(false)
    await boxes[2].setValue(true)
    expect(testApi.collectArgs()).toEqual(['--verbose', '--no-cache', '--quiet'])
  })

  it('必填参数：标签带 *、缺失时提示常驻；补填后红框与提示一并消失', async () => {
    currentArgs.value = [{ name: '--token', flags: ['--token'], dest: 'token', type: 'str', required: true }]
    const w = mount(ArgsForm)

    expect(w.get('label').text()).toContain('*')
    // 未填：底部提示常驻（挂载即出现），但字段尚未标红——标红只发生在点过「运行」之后
    expect(w.findAll('span').some((s) => s.text().includes('存在必填参数'))).toBe(true)
    expect(w.get('input').attributes('aria-invalid')).toBeUndefined()

    // 触发一次收集 = 点「运行」被门禁拦下的那条路径：标红并聚焦首个缺失字段
    testApi.collectArgs()
    await nextTick()
    expect(w.get('input').attributes('aria-invalid')).toBe('true')
    expect(w.get('input').classes()).toContain('border-danger')

    // 补填后红框消失，底部提示也随之消失：校验器读的是「当前值」，不再是
    // 「一旦出现就永久挂着」——后者正是修复前的缺陷（门禁只看 spec，不看已填值）
    await w.get('input').setValue('abc')
    expect(w.get('input').attributes('aria-invalid')).toBeUndefined()
    expect(w.findAll('span').some((s) => s.text().includes('存在必填参数'))).toBe(false)
    expect(testApi.collectArgs()).toEqual(['--token', 'abc'])
  })

  it('必填但有默认值：不算缺失——不提示、不标红，直接可收集', async () => {
    // 语义裁定：必填 ≠ 必须由用户输入，有默认值即视为已满足
    currentArgs.value = [
      { name: '--token', flags: ['--token'], dest: 'token', type: 'str', required: true, default: 'fallback' }
    ]
    const w = mount(ArgsForm)
    // 星标照常显示（它标记 required，不标记「当前缺失」）
    expect(w.get('label').text()).toContain('*')
    expect(w.text()).not.toContain('存在必填参数')
    testApi.collectArgs()
    await nextTick()
    expect(w.get('input').attributes('aria-invalid')).toBeUndefined()
    expect(testApi.collectArgs()).toEqual(['--token', 'fallback'])
  })

  it('sidecar 对无默认值的必填项返回 default: null —— 必须按缺失处理（真实数据形状）', async () => {
    // 回归护栏：曾只判 `default === undefined`，而 sidecar 序列化的是 null，
    // 导致整条必填门禁（提示 / 红框 / runFromCard 拦截）全是死代码
    currentArgs.value = [
      { name: '--token', flags: ['--token'], dest: 'token', type: 'str', required: true, default: null }
    ]
    const w = mount(ArgsForm)
    expect(w.text()).toContain('存在必填参数')
    testApi.collectArgs()
    await nextTick()
    expect(w.get('input').attributes('aria-invalid')).toBe('true')
  })

  it('无必填参数时不出现底部提示', () => {
    currentArgs.value = [{ name: '--a', flags: ['--a'], dest: 'a', type: 'str' }]
    expect(mount(ArgsForm).text()).not.toContain('存在必填参数')
  })

  it('历史回填令牌：flag 匹配取值、布尔置真、其余按位置顺序填充', async () => {
    currentArgs.value = [
      { name: '--name', flags: ['--name'], dest: 'name', type: 'str' },
      { name: '--flag', flags: ['--flag'], dest: 'flag', type: 'bool', action: 'store_true' },
      { name: 'file', flags: [], dest: 'file', type: 'str', is_positional: true }
    ]
    const w = mount(ArgsForm)
    const inputs = w.findAll('input')

    pendingBackfillTokens.value = ['--name', 'bob', '--flag', 'pos.txt']
    await nextTick()

    expect((inputs[0].element as HTMLInputElement).value).toBe('bob')
    expect((inputs[1].element as HTMLInputElement).checked).toBe(true)
    expect((inputs[2].element as HTMLInputElement).value).toBe('pos.txt')
    // 令牌是一次性消费：回填后立即清空，避免后续 currentArgs 变化时重复套用
    expect(pendingBackfillTokens.value).toBeNull()
    expect(testApi.collectArgs()).toEqual(['--name', 'bob', '--flag', 'pos.txt'])
  })

  it('E2E setter 注册：setArgValue 按下标写入字段并参与收集', async () => {
    currentArgs.value = [{ name: '--a', flags: ['--a'], dest: 'a', type: 'str' }]
    const w = mount(ArgsForm)

    testApi.setArgValue(0, 'from-hook')
    await nextTick()
    expect((w.get('input').element as HTMLInputElement).value).toBe('from-hook')
    expect(testApi.collectArgs()).toEqual(['--a', 'from-hook'])
  })
})

// ---------------------------------------------------------------------------
// HistoryPanel
// ---------------------------------------------------------------------------
describe('HistoryPanel', () => {
  it('无历史记录时显示空态文案且没有重跑按钮', () => {
    const w = mount(HistoryPanel)
    expect(w.text()).toContain('该示例还没有运行记录')
    expect(w.find('button').exists()).toBe(false)
  })

  it('成功 / 失败徽章、耗时格式与参数回显', () => {
    selectedId.value = 'e1'
    runHistory.value = [
      makeEntry({ ts: '2026-01-01T10:00:00.000Z', ok: true, exit_code: 0, duration_ms: 500, args: ['--x', '1'] }),
      makeEntry({ ts: '2026-01-01T10:01:00.000Z', ok: false, exit_code: 2, duration_ms: 1500 })
    ]
    const w = mount(HistoryPanel)
    const rows = w.findAll('[class*="justify-between"]')
    expect(rows).toHaveLength(2)

    expect(rows[0].text()).toContain('成功')
    expect(rows[0].text()).toContain('500ms')
    expect(rows[0].text()).toContain('参数 --x 1')
    // v2 状态语言：成功 = 中性文字 + 绿点
    const okRow = rows[0].get('span')
    expect(okRow.classes()).toContain('text-ink-mute')
    expect(okRow.find('.stat-dot').classes()).toContain('bg-ok')

    expect(rows[1].text()).toContain('失败 2')
    // 秒级耗时保留一位小数
    expect(rows[1].text()).toContain('1.5s')
    expect(rows[1].text()).not.toContain('参数')
    expect(rows[1].get('span').classes()).toContain('text-danger')
  })

  it('只展示当前示例的历史，最多 20 条', () => {
    selectedId.value = 'e1'
    runHistory.value = [
      makeEntry({ ts: '2026-01-01T10:00:00.000Z', id: 'other' }),
      ...Array.from({ length: 25 }, (_, i) => makeEntry({ ts: `2026-01-02T10:${String(i).padStart(2, '0')}:00.000Z` }))
    ]
    const w = mount(HistoryPanel)
    expect(w.findAll('[class*="justify-between"]')).toHaveLength(20)
  })

  it('重跑按钮回填记录参数并触发运行', async () => {
    selectedId.value = 'e1'
    examples.value = [makeExample({ id: 'e1', name: 'demo.py' })]
    runHistory.value = [makeEntry({ args: ['--x', '1'] })]
    const w = mount(HistoryPanel)

    await w.get('button[title="回填记录参数并运行"]').trigger('click')
    await flushPromises()

    expect(pendingBackfillTokens.value).toEqual(['--x', '1'])
    expect(isRunning.value).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// OutputPanel
// ---------------------------------------------------------------------------
describe('OutputPanel', () => {
  it('无输出时显示引导文案，未运行时不渲染进度条', () => {
    const w = mount(OutputPanel, { props: { surface: 'detail' } })
    expect(w.text()).toContain('点击「运行」，输出将实时显示在这里')
    expect(w.find('[role="progressbar"]').exists()).toBe(false)
  })

  it('运行中渲染不确定进度条', () => {
    isRunning.value = true
    const w = mount(OutputPanel, { props: { surface: 'runner' } })
    const bar = w.get('[role="progressbar"]')
    expect(bar.attributes('aria-label')).toBe('示例运行中')
    expect(bar.find('.animate-indeterminate').exists()).toBe(true)
  })

  it('按 surface 读取对应输出汇，并按行类型着色', () => {
    surfaceState('detail').lines = [{ text: '普通行', cls: 'base' }]
    surfaceState('runner').lines = [
      { text: '[系统] 系统行', cls: 'system' },
      { text: '[错误] 出错', cls: 'error' },
      { text: '✓ 成功', cls: 'success' }
    ]

    const detail = mount(OutputPanel, { props: { surface: 'detail' } })
    expect(detail.text()).toContain('普通行')
    // 另一个汇的输出不能串台
    expect(detail.text()).not.toContain('系统行')

    const runner = mount(OutputPanel, { props: { surface: 'runner' } })
    const lines = runner.findAll('.whitespace-pre-wrap')
    expect(lines).toHaveLength(3)
    expect(lines[0].text()).toBe('[系统] 系统行')
    expect(lines[0].classes()).toContain('text-gutter')
    expect(lines[0].classes()).toContain('italic')
    expect(lines[1].classes()).toContain('text-danger')
    expect(lines[2].classes()).toContain('text-ok')
  })

  it('截断态渲染系统提示行', () => {
    const state = surfaceState('detail')
    state.lines = [{ text: '最后一行', cls: 'base' }]
    state.truncated = true
    const w = mount(OutputPanel, { props: { surface: 'detail' } })
    expect(w.text()).toContain('输出超过上限，已自动截断，仅保留最近的输出')
    expect(w.text()).toContain('最后一行')
  })

  it('有图片时渲染缩略图与文件名，下载按钮调用 sidecar', async () => {
    surfaceState('detail').images = [{ url: 'file:///tmp/out.png', name: 'out.png' }]
    const w = mount(OutputPanel, { props: { surface: 'detail' } })

    expect(w.text()).toContain('运行结果图片')
    expect(w.get('img').attributes('src')).toBe('file:///tmp/out.png')
    expect(w.get('img').attributes('alt')).toBe('out.png')
    expect(w.get('figcaption').text()).toContain('out.png')

    await w.get('button').trigger('click')
    await flushPromises()
    expect(vi.mocked(window.sidecar.downloadResultImage)).toHaveBeenCalledWith('file:///tmp/out.png', 'out.png')
  })

  it('无图片时不渲染图片区', () => {
    const w = mount(OutputPanel, { props: { surface: 'detail' } })
    expect(w.text()).not.toContain('运行结果图片')
    expect(w.find('img').exists()).toBe(false)
  })
})

// ---------------------------------------------------------------------------
describe('GalleryHeader 跟随二级分区（用户语义：选了分区，右侧就是分区的示例）', () => {
  it('分区激活时：标题=分区名，统计=分区内口径（示例数/可运行/收藏），主题 chip 退场', async () => {
    examples.value = [
      makeExample({ id: 't1', name: 'a.py', theme_key: 'turtle', run_status: 'runnable' }),
      makeExample({ id: 't2', name: 'b.py', theme_key: 'turtle', run_status: 'runnable' }),
      makeExample({ id: 't3', name: 'c.py', theme_key: 'turtle', run_status: 'missing_deps' }),
      makeExample({ id: 'g1', name: 'd.py', theme_key: 'games', run_status: 'runnable' })
    ]
    favorites.value = new Set(['t1', 'g1'])
    activeSectionKey.value = 'turtle'
    await nextTick()
    const w = mount(GalleryHeader)

    expect(w.get('h1').text()).toBe('Turtle 绘图')
    const chips = w.findAll('.stat-chip')
    // 分区池 = 3 条 turtle（games 不算）；可运行 2/3=67%；收藏只数分区内（g1 不算）
    expect(chips.map((c) => c.text())).toEqual(['3 个示例', '67% 可运行', '1 收藏'])
    // 浏览全部仍是退出分区的入口
    expect(w.findAll('button').some((b) => b.text() === '浏览全部')).toBe(true)
  })

  it('分区激活时收藏 chip 统计分区内收藏，不是全局收藏数', async () => {
    examples.value = [
      makeExample({ id: 't1', name: 'a.py', theme_key: 'turtle', run_status: 'runnable' }),
      makeExample({ id: 'g1', name: 'd.py', theme_key: 'games', run_status: 'runnable' })
    ]
    favorites.value = new Set(['t1', 'g1'])
    activeSectionKey.value = 'turtle'
    await nextTick()
    const w = mount(GalleryHeader)
    expect(w.findAll('.stat-chip').map((c) => c.text())).toEqual(['1 个示例', '100% 可运行', '1 收藏'])
  })
})
