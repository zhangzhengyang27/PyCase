// 交互工具黄金对拍（TS 侧）：tool-schemas 的 compute 输出逐条比对 tool-golden.json
// （Python 参考实现自校验在 tests/test_tool_golden.py——同一份 JSON，双端唯一事实）。
// pyCode 是 TS 模板，Python 无法执行——片段断言钉关键行 + 落地时的真实产物抽查。
import { describe, expect, it } from 'vitest'
import { getToolSchema } from '../interactive-tools'
import golden from '../tool-golden.json'

const temp = getToolSchema('interactive:temp-convert')!
const base = getToolSchema('interactive:base-convert')!
const caesar = getToolSchema('interactive:caesar-cipher')!

describe('温度换算器 ↔ 黄金用例', () => {
  it.each(golden.temp.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = temp.compute!({ value: c.value, from: c.from, to: c.to, precision: c.precision })
    if ('error' in c.expected) {
      expect(r.error).toBe(c.expected.error)
      return
    }
    expect(r.error).toBeUndefined()
    expect(r.primary?.value).toBe(c.expected.primary)
    expect(Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))).toEqual(c.expected.rows)
  })
})

describe('进制转换器 ↔ 黄金用例', () => {
  it.each(golden.base.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = base.compute!({ value: c.value, fromBase: c.fromBase })
    if ('error' in c.expected) {
      expect(r.error).toBe(c.expected.error)
      return
    }
    expect(r.error).toBeUndefined()
    expect(Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))).toEqual(c.expected.rows)
  })
})

describe('凯撒密码 ↔ 黄金用例', () => {
  it.each(golden.caesar.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = caesar.compute!({ text: c.text, shift: c.shift, mode: c.mode })
    expect(r.error).toBeUndefined()
    expect(r.primary?.value).toBe(c.expected.primary)
    // 回验行恒等于原文（加密↔解密互逆）
    expect(r.rows?.[1]?.value).toBe(c.text)
  })
})

describe('pyCode 模板关键片段', () => {
  it('温度：Kelvin 锚点与格式化位数', () => {
    const code = temp.pyCode!({ value: 36.6, from: 'C', to: 'F', precision: '2' })
    expect(code).toContain('v = float("36.6")')
    expect(code).toContain('{c:.2f}')
    expect(code).toContain('k = v + 273.15 if "C"')
  })
  it('进制：int(s, base) 解析与四进制循环', () => {
    const code = base.pyCode!({ value: 'ff', fromBase: '16' })
    expect(code).toContain('int("ff", 16)')
    expect(code).toContain('for base in (2, 8, 10, 16)')
  })
  it('凯撒：归一移位与回验', () => {
    const code = caesar.pyCode!({ text: 'abc', shift: 29, mode: 'encrypt' })
    expect(code).toContain('caesar(msg, 3)')
    expect(code).toContain('caesar(result, -3)')
  })
  it('输入不完整 → 引导注释（可直接展示，无失败路径）', () => {
    expect(temp.pyCode!({ value: '', from: 'C', to: 'F', precision: '1' })).toContain('# 补全输入')
    expect(caesar.pyCode!({ text: '', shift: 3, mode: 'encrypt' })).toContain('# 补全输入')
  })
})

describe('注册表联动', () => {
  it('三工具已注册且卡片派生', async () => {
    const { interactiveToolItems } = await import('../interactive-tools')
    const ids = interactiveToolItems.value.map((t) => t.id)
    expect(ids).toContain('interactive:temp-convert')
    expect(ids).toContain('interactive:base-convert')
    expect(ids).toContain('interactive:caesar-cipher')
  })
})

// ---------------------------------------------------------------------------
// W2：文本折行 / 回文判定
// ---------------------------------------------------------------------------
const wrap = getToolSchema('interactive:text-wrap')!
const pal = getToolSchema('interactive:palindrome')!

describe('文本折行 ↔ 黄金用例', () => {
  it.each(golden.wrap.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = wrap.compute!({ text: c.text, width: c.width })
    expect(r.error).toBeUndefined()
    expect(r.primary?.value).toBe(c.expected.primary)
    expect(r.text).toBe(c.expected.text)
  })
  it('列宽非法 → 引导文案', () => {
    expect(wrap.compute!({ text: 'abc', width: 0 })!.error).toContain('列宽')
    expect(wrap.compute!({ text: '', width: 28 })!.error).toContain('请输入文本')
  })
})

describe('回文判定 ↔ 黄金用例', () => {
  it.each(golden.palindrome.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = pal.compute!({ text: c.text })
    expect(r.error).toBeUndefined()
    expect(r.primary?.value).toBe(c.expected.primary)
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows['归一化后']).toBe(c.expected.norm || '（空）')
    if ('mismatch' in c.expected && Array.isArray(c.expected.mismatch)) {
      const [i, a, b] = c.expected.mismatch as [number, string, string]
      expect(rows['首处差异']).toBe(`第 ${i} 位 '${a}' ≠ '${b}'`)
    } else {
      expect(rows['首处差异']).toBeUndefined()
    }
  })
  it('空文本 → 引导文案', () => {
    expect(pal.compute!({ text: '' })!.error).toContain('请输入文本')
  })
})

describe('W2 pyCode 关键片段', () => {
  it('折行：greedy 循环与行数输出', () => {
    const code = wrap.pyCode!({ text: 'a b c', width: 2 })
    expect(code).toContain('width = 2')
    expect(code).toContain('共 {len(lines)} 行')
  })
  it('回文：isalnum 归一与双指针', () => {
    const code = pal.pyCode!({ text: 'LeVeL' })
    expect(code).toContain('ch.isalnum()')
    expect(code).toContain('s = "LeVeL"')
  })
  it('输入不完整 → 引导注释', () => {
    expect(wrap.pyCode!({ text: '', width: 28 })).toContain('# 补全输入')
    expect(pal.pyCode!({ text: '  ' })).toContain('# 补全输入')
  })
})
