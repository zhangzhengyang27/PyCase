// InteractiveToolPage：schema 表单渲染、compute 实时联动、抽屉接收 pyCode、返回清选中。
// 用假 schema 驱动（真实 schema 在 T5-T7 各自的黄金测试里钉）。
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

import { mount, flushPromises } from '@vue/test-utils'
import InteractiveToolPage from '../interactive/InteractiveToolPage.vue'
import { interactiveToolSchemas, type InteractiveToolSchema } from '../../src/interactive-tools'
import { toolValues } from '../../src/store/interactive'
import { runContext, runImages, runOutput } from '../../src/store/date-run'
import { selectedId, pendingPreset } from '../../src/store/detail'

const dummy: InteractiveToolSchema = {
  id: 'interactive:dummy-page',
  title: '页面假想工具',
  description: 'T4 测试用。',
  tags: ['测试'],
  fields: [
    { key: 'name', label: '名称', type: 'text', default: 'abc', required: true },
    { key: 'times', label: '倍数', type: 'number', default: 2 }
  ],
  compute: (v) => {
    const name = String(v.name ?? '')
    if (!name) return { error: '请输入名称' }
    return { primary: { value: name.repeat(Number(v.times ?? 1)) } }
  },
  pyCode: (v) => `print(${JSON.stringify(String(v.name ?? ''))})\n`
}

// headerFor 联动测试用：类型选择驱动的实验室形态页
const typed: InteractiveToolSchema = {
  id: 'interactive:dummy-typed',
  title: '类型实验室',
  description: '静态描述。',
  tags: ['测试'],
  fields: [
    {
      key: 'type',
      label: '类型',
      type: 'select',
      default: 'a',
      options: [
        { value: 'a', label: '甲' },
        { value: 'b', label: '乙' }
      ]
    }
  ],
  headerFor: (v) => (v.type === 'b' ? { title: '乙型', description: '乙的描述。' } : { title: '甲型', description: '甲的描述。' }),
  compute: (v) => ({ primary: { value: String(v.type ?? '') } }),
  pyCode: () => 'print(1)\n'
}

// sidecar 计算型：运行产物图预览测试用
const imgTool: InteractiveToolSchema = {
  id: 'interactive:dummy-img',
  title: '图像工具',
  description: '运行产物图测试用。',
  tags: ['测试'],
  fields: [],
  computeVia: 'sidecar',
  compute: () => ({}),
  pyCode: () => 'print(1)\n'
}

// sidecar 实验室形态：运行结果按「页面+类型」上下文隔离的测试用
const labTool: InteractiveToolSchema = {
  id: 'interactive:dummy-lab',
  title: '仿真实验室',
  description: '上下文隔离测试用。',
  tags: ['测试'],
  fields: [
    {
      key: 'type',
      label: '类型',
      type: 'select',
      default: 'a',
      options: [
        { value: 'a', label: '甲' },
        { value: 'b', label: '乙' }
      ]
    }
  ],
  computeVia: 'sidecar',
  compute: () => ({}),
  pyCode: () => 'print(1)\n'
}

beforeEach(() => {
  interactiveToolSchemas.push(dummy, typed, imgTool, labTool)
  toolValues.value = {}
  selectedId.value = dummy.id
  pendingPreset.value = null
  runOutput.value = ''
  runImages.value = []
  runContext.value = null
})
afterEach(() => {
  for (const s of [dummy, typed, imgTool, labTool]) {
    const i = interactiveToolSchemas.findIndex((x) => x.id === s.id)
    if (i >= 0) interactiveToolSchemas.splice(i, 1)
  }
})

describe('InteractiveToolPage', () => {
  it('按 schema 渲染表单与默认结果', () => {
    const w = mount(InteractiveToolPage)
    expect(w.text()).toContain('页面假想工具')
    expect(w.findAll('input')).toHaveLength(2)
    expect(w.find('[data-testid="tool-primary"]').text()).toContain('abcabc')
  })
  it('输入联动：改字段即时重算', async () => {
    const w = mount(InteractiveToolPage)
    const inputs = w.findAll('input')
    await inputs[1]!.setValue('3')
    expect(w.find('[data-testid="tool-primary"]').text()).toContain('abcabcabc')
  })
  it('required 置空 → 结果区显示 error 引导', async () => {
    const w = mount(InteractiveToolPage)
    await w.findAll('input')[0]!.setValue('')
    expect(w.find('[data-testid="tool-error"]').text()).toContain('请输入名称')
  })
  it('抽屉接收 pyCode 产物（复制内容 = pyCode(values)）', async () => {
    const clipboardWrite = vi.fn<(code: string) => Promise<void>>(async () => {})
    Object.assign(navigator, { clipboard: { writeText: clipboardWrite } })
    const w = mount(InteractiveToolPage)
    await w.find('[data-testid="drawer-toggle"]').trigger('click')
    await w.find('[data-testid="drawer-copy"]').trigger('click')
    expect(clipboardWrite).toHaveBeenCalledWith('print("abc")\n')
  })
  it('返回按钮清空 selectedId', async () => {
    const w = mount(InteractiveToolPage)
    await w.find('[data-testid="it-back"]').trigger('click')
    expect(selectedId.value).toBeNull()
  })
  it('未知交互 id → 兜底文案（不崩溃）', () => {
    selectedId.value = 'interactive:ghost'
    const w = mount(InteractiveToolPage)
    expect(w.text()).toContain('工具不存在或已下线')
  })
  it('headerFor 联动：页头标题/描述随类型选择实时变化', async () => {
    selectedId.value = typed.id
    const w = mount(InteractiveToolPage)
    expect(w.find('h1').text()).toBe('甲型')
    expect(w.text()).toContain('甲的描述。')
    await w.find('select').setValue('b')
    expect(w.find('h1').text()).toBe('乙型')
    expect(w.text()).toContain('乙的描述。')
  })
  it('预选进入即锁型：类型选择器隐藏，页头仍显示该类型', async () => {
    pendingPreset.value = { pageId: typed.id, values: { type: 'b' } }
    selectedId.value = typed.id
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.find('h1').text()).toBe('乙型')
    expect(w.findAll('select')).toHaveLength(0)
    expect(w.text()).toContain('乙的描述。')
    w.unmount()
  })
  it('无预选进入不锁型：类型选择器保留（实验室探索形态）', async () => {
    selectedId.value = typed.id
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.findAll('select')).toHaveLength(1)
    w.unmount()
  })
  it('同实例换页重置锁型：锁型页切走再无预选切回，类型选择器恢复', async () => {
    pendingPreset.value = { pageId: typed.id, values: { type: 'b' } }
    selectedId.value = typed.id
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.findAll('select')).toHaveLength(0)
    selectedId.value = dummy.id
    await flushPromises()
    selectedId.value = typed.id
    await flushPromises()
    expect(w.findAll('select')).toHaveLength(1)
    w.unmount()
  })
  it('sidecar 页运行产物图直接呈现在结果区（上下文匹配时）', async () => {
    selectedId.value = imgTool.id
    runContext.value = 'interactive:dummy-img|'
    runImages.value = ['file:///ws/chart.png']
    const w = mount(InteractiveToolPage)
    await flushPromises()
    const strip = w.find('[data-testid="page-run-images"]')
    expect(strip.exists()).toBe(true)
    expect(strip.find('img').attributes('src')).toBe('file:///ws/chart.png')
    w.unmount()
  })
  it('运行结果按上下文隔离：重进同一实验室的另一类型，不显示上次运行（用户报的串页 bug）', async () => {
    // 上次在类型 a 上运行过；返回后再点类型 b 的家族卡进入
    runContext.value = 'interactive:dummy-lab|a'
    runOutput.value = '已输出 chart.png'
    runImages.value = ['file:///ws/chart.png']
    pendingPreset.value = { pageId: 'interactive:dummy-lab', values: { type: 'b' } }
    selectedId.value = 'interactive:dummy-lab'
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.find('[data-testid="page-run-images"]').exists()).toBe(false)
    expect(w.text()).not.toContain('已输出 chart.png')
    expect(w.find('[data-testid="page-run"]').text()).toContain('运行')
    expect(w.find('[data-testid="page-run"]').text()).not.toContain('重新运行')
    w.unmount()
  })
  it('同上下文重进：上次运行结果恢复显示（同一家族卡来回看）', async () => {
    runContext.value = 'interactive:dummy-lab|a'
    runOutput.value = '已输出 chart.png'
    pendingPreset.value = { pageId: 'interactive:dummy-lab', values: { type: 'a' } }
    selectedId.value = 'interactive:dummy-lab'
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.text()).toContain('已输出 chart.png')
    expect(w.find('[data-testid="page-run"]').text()).toContain('重新运行')
    w.unmount()
  })
  it('未锁型页内切换类型：旧类型的运行结果不再显示', async () => {
    runContext.value = 'interactive:dummy-lab|a'
    runOutput.value = '已输出 chart.png'
    selectedId.value = 'interactive:dummy-lab'
    const w = mount(InteractiveToolPage)
    await flushPromises()
    expect(w.text()).toContain('已输出 chart.png')
    await w.findAll('select')[0]!.setValue('b')
    await flushPromises()
    expect(w.text()).not.toContain('已输出 chart.png')
    w.unmount()
  })
})
