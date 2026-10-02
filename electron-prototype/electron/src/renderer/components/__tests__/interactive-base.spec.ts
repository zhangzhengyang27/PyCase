// ToolField / ToolResultPanel：schema 表单原子件与结果渲染（T3）。
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ToolField from '../interactive/ToolField.vue'
import ToolResultPanel from '../interactive/ToolResultPanel.vue'
import type { FieldSpec, ToolResult } from '../../src/interactive-tools'

const clipboardWrite = vi.fn<(code: string) => Promise<void>>(async () => {})
Object.assign(navigator, { clipboard: { writeText: clipboardWrite } })

describe('ToolField', () => {
  const textSpec: FieldSpec = { key: 'a', label: '文本', type: 'text', default: 'x', required: true }
  const selectSpec: FieldSpec = {
    key: 'u',
    label: '单位',
    type: 'select',
    default: 'C',
    options: [
      { value: 'C', label: '摄氏' },
      { value: 'F', label: '华氏' }
    ]
  }
  const areaSpec: FieldSpec = { key: 't', label: '大段', type: 'textarea', placeholder: '粘这里' }
  const checkSpec: FieldSpec = { key: 'c', label: '开关', type: 'checkbox', default: false, help: '启用增强' }

  it('text：输入回写 number 不转（保持字符串）', async () => {
    const w = mount(ToolField, { props: { spec: textSpec, modelValue: 'x' } })
    await w.find('input').setValue('hello')
    expect(w.emitted('update:modelValue')![0]).toEqual(['hello'])
  })
  it('number：输入转 Number，空串回写 undefined', async () => {
    const w = mount(ToolField, { props: { spec: { key: 'n', label: '数值', type: 'number' }, modelValue: undefined } })
    await w.find('input').setValue('12.5')
    expect(w.emitted('update:modelValue')![0]).toEqual([12.5])
    await w.find('input').setValue('')
    expect(w.emitted('update:modelValue')![1]).toEqual([undefined])
  })
  it('required 缺失时 invalid → border-danger', () => {
    const w = mount(ToolField, { props: { spec: textSpec, modelValue: undefined, invalid: true } })
    expect(w.find('input').classes().join(' ')).toContain('border-danger')
  })
  it('select：选项渲染与回写', async () => {
    const w = mount(ToolField, { props: { spec: selectSpec, modelValue: 'C' } })
    expect(w.findAll('option')).toHaveLength(2)
    await w.find('select').setValue('F')
    expect(w.emitted('update:modelValue')![0]).toEqual(['F'])
  })
  it('textarea 与 checkbox 回写', async () => {
    const wa = mount(ToolField, { props: { spec: areaSpec, modelValue: '' } })
    await wa.find('textarea').setValue('line1\nline2')
    expect(wa.emitted('update:modelValue')![0]).toEqual(['line1\nline2'])
    const wc = mount(ToolField, { props: { spec: checkSpec, modelValue: false } })
    await wc.find('input[type="checkbox"]').setValue(true)
    expect(wc.emitted('update:modelValue')![0]).toEqual([true])
  })
})

describe('ToolResultPanel', () => {
  it('error 形态：只渲染引导文案', () => {
    const r: ToolResult = { error: '请先输入一个数' }
    const w = mount(ToolResultPanel, { props: { result: r } })
    expect(w.find('[data-testid="tool-error"]').text()).toBe('请先输入一个数')
    expect(w.find('[data-testid="tool-primary"]').exists()).toBe(false)
  })
  it('primary + rows 渲染', () => {
    const r: ToolResult = {
      primary: { value: '98.6', unit: '℉' },
      rows: [
        { label: '摄氏', value: '37.0 ℃' },
        { label: '开尔文', value: '310.2 K', copy: true }
      ]
    }
    const w = mount(ToolResultPanel, { props: { result: r } })
    expect(w.find('[data-testid="tool-primary"]').text()).toContain('98.6')
    expect(w.find('[data-testid="tool-rows"]').text()).toContain('310.2 K')
  })
  it('rows 行复制写剪贴板', async () => {
    const r: ToolResult = { rows: [{ label: 'HEX', value: '#ff0000', copy: true }] }
    const w = mount(ToolResultPanel, { props: { result: r } })
    await w.find('[aria-label="复制 HEX"]').trigger('click')
    expect(clipboardWrite).toHaveBeenCalledWith('#ff0000')
  })
  it('text 与 list 渲染，list 逐行可复制', async () => {
    const r: ToolResult = { text: 'line1\nline2', list: ['id-1', 'id-2'] }
    const w = mount(ToolResultPanel, { props: { result: r } })
    expect(w.find('[data-testid="tool-text"]').text()).toContain('line2')
    expect(w.findAll('[data-testid="tool-list"] li')).toHaveLength(2)
    await w.find('[aria-label="复制第 2 项"]').trigger('click')
    expect(clipboardWrite).toHaveBeenCalledWith('id-2')
  })
})
