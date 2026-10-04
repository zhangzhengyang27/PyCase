// 注册表与工具池合并：交互工具恒置顶、参与收藏过滤；不计入可运行率分母口径。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import {
  activeToolCategory,
  catalogToolsTotal,
  examples,
  favOnly,
  toolboxCategoryNav,
  toolboxItems,
  toolsTotal,
  toolSearchQuery,
  type VExample
} from '../store/catalog'
import { TOOL_CATEGORY_CATALOG, toolCategoryKeyOf } from '../toolbox-cats'
import { DATE_CALC_ID, INTERACTIVE_GROUP_KEY, interactiveToolItems, isInteractiveId } from '../interactive-tools'
import { toolboxIcon } from '../section-icons'
import { favorites } from '../store/prefs'
import { getTestApi } from '../store/index'

function seedTools(): void {
  examples.value = [
    {
      id: 'tools_x1',
      name: 'x1.py',
      category: 'tools',
      path: 'tools/x1.py',
      run_status: 'runnable',
      quality_score: 80
    },
    {
      id: 'tools_x2',
      name: 'x2.py',
      category: 'tools',
      path: 'tools/x2.py',
      run_status: 'broken'
    }
  ]
}

beforeEach(() => {
  seedTools()
  favOnly.value = false
  favorites.value = new Set()
})

describe('toolboxItems 合并交互工具', () => {
  it('交互工具置顶且目录池照旧', () => {
    expect(toolboxItems.value[0]?.id).toBe(DATE_CALC_ID)
    expect(toolboxItems.value.map((t) => t.id)).toContain('tools_x1')
  })
  it('收藏过滤作用于交互工具', () => {
    favOnly.value = true
    expect(toolboxItems.value).toHaveLength(0)
    favorites.value = new Set([DATE_CALC_ID])
    expect(toolboxItems.value.map((t) => t.id)).toEqual([DATE_CALC_ID])
  })
  it('toolsTotal 含交互工具，catalogToolsTotal 不含', () => {
    expect(catalogToolsTotal.value).toBe(2)
    // 目录池 2 + 交互注册表 126（… + W15×4）
    expect(toolsTotal.value).toBe(143)
  })
  it('isInteractiveId 前缀判定', () => {
    expect(isInteractiveId(DATE_CALC_ID)).toBe(true)
    expect(isInteractiveId('topics_x')).toBe(false)
    expect(isInteractiveId(undefined)).toBe(false)
  })
  it('INTERACTIVE_GROUP_KEY 钉住工具箱分组图标映射（键漂移会静默退化成 Wrench 且无报错）', () => {
    expect(toolboxIcon(INTERACTIVE_GROUP_KEY)).toBe(Sparkles)
  })
  it('注册表条目不含 run_status（不进可运行域）', () => {
    expect(interactiveToolItems.value.every((t) => t.run_status === undefined)).toBe(true)
  })
  it('搜索词命中交互工具（name 口径，debounce 后生效）', async () => {
    // appliedToolSearch 是模块私有 ref，由 toolSearchQuery 的 watch 防抖 120ms 写入；
    // 与 browse.spec 同一推法：fake timers 推进防抖窗口，再断言合并池仍含交互工具。
    // 'date' 只存在于 name 'date-calculator'（title/description/tags 均中文），专测 name 口径。
    vi.useFakeTimers()
    toolSearchQuery.value = 'date'
    await nextTick()
    vi.advanceTimersByTime(120)
    await nextTick()
    vi.useRealTimers()
    expect(toolboxItems.value.map((t) => t.id)).toContain(DATE_CALC_ID)
  })
})

// ---------------------------------------------------------------------------
// T2：schema 注册表——派生卡片、按 id 查找、工具输入值初始化
// ---------------------------------------------------------------------------
import { interactiveToolSchemas, getToolSchema, type FieldSpec, type InteractiveToolSchema } from '../interactive-tools'
import { toolValues, toolValueOf } from '../store/interactive'

const dummySchema: InteractiveToolSchema = {
  id: 'interactive:dummy-tool',
  title: '假想工具',
  description: '仅用于注册表派生测试。',
  tags: ['测试'],
  fields: [
    { key: 'a', label: '甲', type: 'text', default: 'x' },
    { key: 'b', label: '乙', type: 'number', required: true }
  ],
  compute: () => ({}),
  pyCode: () => 'print(1)\n'
}

describe('schema 注册表', () => {
  beforeEach(() => {
    toolValues.value = {}
  })
  it('注册 schema 后自动派生卡片（无 run_status，进工具池）', () => {
    interactiveToolSchemas.push(dummySchema)
    try {
      const card = interactiveToolItems.value.find((t) => t.id === dummySchema.id)
      expect(card).toBeTruthy()
      expect(card!.title).toBe('假想工具')
      expect(card!.category).toBe('tools')
      expect(card!.run_status).toBeUndefined()
      expect(getToolSchema(dummySchema.id)).toEqual(dummySchema)
      expect(getToolSchema('interactive:none')).toBeUndefined()
    } finally {
      interactiveToolSchemas.pop()
    }
  })
  it('toolValueOf 首次按 defaults 初始化并复用同一对象', () => {
    const v1 = toolValueOf(dummySchema.id, dummySchema.fields as FieldSpec[])
    expect(v1).toEqual({ a: 'x', b: undefined })
    v1.a = 'changed'
    const v2 = toolValueOf(dummySchema.id, dummySchema.fields as FieldSpec[])
    expect(v2).toBe(v1)
    expect(v2.a).toBe('changed')
  })
})

describe('工具箱分类（W16 二级菜单）', () => {
  beforeEach(() => {
    activeToolCategory.value = null
    // resetViewFilters 同步清 appliedToolSearch（防抖 ref 不能靠赋值 toolSearchQuery 复位）
    ;(getTestApi() as { resetViewFilters: () => void }).resetViewFilters()
    favOnly.value = false // 防上游用例泄漏：favOnly=true 会把未收藏条目全滤光
    seedTools()
  })
  it('分类规则抽样：标题/标签 → 分类 key', () => {
    expect(toolCategoryKeyOf({ title: '正则测试器', tags: ['文本'] })).toBe('text')
    expect(toolCategoryKeyOf({ title: '图片批量水印', tags: ['图片'] })).toBe('image')
    expect(toolCategoryKeyOf({ title: 'Git 提交统计', tags: ['Git'] })).toBe('git')
    expect(toolCategoryKeyOf({ title: '网速测试', tags: ['网络'] })).toBe('net')
    expect(toolCategoryKeyOf({ title: '电池状态监控', tags: ['系统'] })).toBe('sysmon')
    expect(toolCategoryKeyOf({ title: '敏感文件粉碎器', tags: ['安全'] })).toBe('sec')
    expect(toolCategoryKeyOf({ title: '温度换算器', tags: ['换算'] })).toBe('conv')
    expect(toolCategoryKeyOf({ title: 'rename_weeks.py', name: 'rename_weeks.py' })).toBe('teach') // 无正标题+纯文件名 = migrated 课程脚本
    expect(toolCategoryKeyOf({ title: '某工具', tags: [] })).toBe('other')
  })
  it('toolboxCategoryNav：全量池计数（不随 activeToolCategory 变化）', () => {
    const nav = toolboxCategoryNav.value
    expect(nav.map((n) => n.key)).toEqual(TOOL_CATEGORY_CATALOG.map((c) => c.key))
    const total = nav.reduce((acc, n) => acc + n.count, 0)
    // 全量池 = 交互注册表（2 专属卡 + 全部 schema）+ fixture 目录池 2
    expect(total).toBe(interactiveToolItems.value.length + 2)
  })
  it('activeToolCategory 过滤 toolboxItems（目录池与注册表两侧）', () => {
    examples.value = [
      { id: 'tools_img', name: 'img.py', title: '图片工具', category: 'tools', path: 'p', tags: ['图片'] },
      { id: 'tools_git', name: 'g.py', title: 'Git 工具', category: 'tools', path: 'p', tags: ['Git'] }
    ] as VExample[]
    activeToolCategory.value = 'image'
    const ids = toolboxItems.value.map((t) => t.id)
    expect(ids).toContain('tools_img')
    expect(ids.every((id) => toolCategoryKeyOf({ title: id, tags: ['图片'] }) === 'image')).toBe(true)
    activeToolCategory.value = null
    expect(toolboxItems.value.length).toBe(interactiveToolItems.value.length + 2)
  })
})

// ---------------------------------------------------------------------------
// 实验室页头联动：headerFor 必须覆盖全部类型档位，标题/描述与类型注册表一致。
// 背景：家族卡进入实验室页时页头曾恒显归并页名（如「turtle 图形画廊」），
// 且路由预选键 type 与 turtle/pil/cv 的类型字段键（shape/filter/op）不一致被静默丢弃。
// 本用例同时钉住「类型选择器 key 统一为 type」与「headerFor 全档位覆盖」两个不变量。
describe('实验室页头联动（headerFor 全档位）', () => {
  const LABS = [
    'interactive:viz-lab',
    'interactive:pil-lab',
    'interactive:cv-lab',
    'interactive:turtle-lab',
    'interactive:sciviz-lab',
    'interactive:basics-lab',
    'interactive:crawler-lab',
    'interactive:pandas-lab'
  ]
  for (const id of LABS) {
    it(`${id}：全档位标题/描述与类型注册表一致`, () => {
      const s = getToolSchema(id)
      expect(s, `${id} 未注册`).toBeTruthy()
      const f0 = typeof s!.fields === 'function' ? s!.fields({}) : s!.fields
      const tf = f0.find((f) => f.key === 'type')
      expect(tf, `${id} 缺少 key='type' 的类型选择器`).toBeTruthy()
      const opts = tf!.options as Array<{ value: string; label: string }>
      expect(opts.length).toBeGreaterThan(0)
      for (const o of opts) {
        const h = s!.headerFor?.({ type: o.value })
        expect(h, `类型 ${o.value} 无页头信息`).toBeDefined()
        expect(h!.title).toBe(o.label)
        expect(h!.description.trim()).not.toBe('')
      }
    })
  }
})
