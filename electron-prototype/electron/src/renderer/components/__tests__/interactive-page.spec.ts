// InteractiveToolPage：schema 表单渲染、compute 实时联动、抽屉接收 pyCode、返回清选中。
// 用假 schema 驱动（真实 schema 在 T5-T7 各自的黄金测试里钉）。
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../monaco', () => ({
  monaco: { editor: { create: vi.fn(() => ({ setValue: vi.fn(), dispose: vi.fn() })) } },
  applyMonacoTheme: vi.fn(),
  currentMonacoTheme: () => 'test'
}))

import { mount } from '@vue/test-utils'
import InteractiveToolPage from '../interactive/InteractiveToolPage.vue'
import { interactiveToolSchemas, type InteractiveToolSchema } from '../../src/interactive-tools'
import { toolValues } from '../../src/store/interactive'
import { selectedId } from '../../src/store/detail'

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

beforeEach(() => {
  interactiveToolSchemas.push(dummy)
  toolValues.value = {}
  selectedId.value = dummy.id
})
afterEach(() => {
  const i = interactiveToolSchemas.findIndex((s) => s.id === dummy.id)
  if (i >= 0) interactiveToolSchemas.splice(i, 1)
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
})
