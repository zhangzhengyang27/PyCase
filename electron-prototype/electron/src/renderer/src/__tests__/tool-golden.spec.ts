// 交互工具黄金对拍（TS 侧）：tool-schemas 的 compute 输出逐条比对 tool-golden.json
// （Python 参考实现自校验在 tests/test_tool_golden.py——同一份 JSON，双端唯一事实）。
// pyCode 是 TS 模板，Python 无法执行——片段断言钉关键行 + 落地时的真实产物抽查。
import { describe, expect, it } from 'vitest'
import { getToolSchema, type FieldValue } from '../interactive-tools'
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

// ---------------------------------------------------------------------------
// W3：devtools 九工具（确定性八段走黄金对拍；uuid 随机型只钉格式与唯一性）
// ---------------------------------------------------------------------------
const dev = (id: string) => getToolSchema(id)!

describe('正则测试器 ↔ 黄金用例', () => {
  it.each(golden.regex.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:regex-tester').compute!({ pattern: c.pattern, sample: c.sample, ...c.flags })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    expect(r.error).toBeUndefined()
    expect(r.primary?.value).toBe(c.expected.primary)
    expect(r.list).toEqual(c.expected.list)
  })
})

describe('JSON 格式化 ↔ 黄金用例', () => {
  it.each(golden.jsonfmt.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:json-format').compute!({ input: c.input, indent: c.indent })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    expect(r.text).toBe(c.expected.text)
  })
})

describe('CSV ↔ JSON ↔ 黄金用例', () => {
  it.each(golden.csvjson.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:csv-json').compute!({ direction: c.direction, input: c.input })
    expect(r.text).toBe(c.expected.text)
  })
})

describe('时间戳转换 ↔ 黄金用例（UTC 口径）', () => {
  it.each(golden.ts.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:timestamp').compute!({ mode: c.mode, unit: c.unit ?? 's', value: c.value })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows['UTC']).toBe(c.expected.utc)
    expect(rows['ISO 8601']).toBe(c.expected.iso)
    if (c.expected.seconds) expect(rows['秒']).toBe(c.expected.seconds)
  })
})

describe('颜色转换器 ↔ 黄金用例', () => {
  it.each(golden.color.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:color').compute!({ value: c.value })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows['HEX']).toBe(c.expected.hex)
    expect(rows['RGB']).toBe(c.expected.rgb)
    expect(rows['HSL']).toBe(c.expected.hsl)
  })
})

describe('科学单位换算 ↔ 黄金用例', () => {
  it.each(golden.unit.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:unit-convert').compute!({ dim: c.dim, value: c.value, from: c.from, to: c.to })
    expect(r.primary?.value).toBe(c.expected.value)
  })
  it('单位选项随量纲联动（options 函数形态）', () => {
    const schema = dev('interactive:unit-convert')!
    const fromField = (Array.isArray(schema.fields) ? schema.fields : schema.fields({}))!.find((f) => f.key === 'from')!
    expect(typeof fromField.options).toBe('function')
    const opts = (fromField.options as (v: Record<string, unknown>) => { value: string }[])({ dim: '质量' })
    expect(opts.map((o) => o.value)).toContain('lb')
    expect(opts.map((o) => o.value)).not.toContain('km')
  })
})

describe('密码强度检查 ↔ 黄金用例', () => {
  it.each(golden.pwd.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:pwd-strength').compute!({ value: c.value })
    expect(r.primary?.value).toBe(c.expected.score)
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows['强度']).toBe(c.expected.label)
    expect(rows['常见弱口令']).toBe(c.expected.common.length ? c.expected.common.join(', ') : '未命中')
  })
})

describe('JSON → dataclass ↔ 黄金用例', () => {
  it.each(golden.dataclass.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:json-dataclass').compute!({ input: c.input, className: c.className })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    expect(r.text).toBe(c.expected.text)
  })
})

describe('UUID 生成（随机型：格式 + 唯一性）', () => {
  const spec = golden.uuid
  it.each([
    ['uuid4', 'uuid4', spec.uuid4_pattern],
    ['short', 'short', spec.short_pattern]
  ] as const)('%s 格式与唯一性', (_name, mode, pattern) => {
    const schema = dev('interactive:uuid')!
    const r = schema.compute!({ mode, count: 20 })
    const list = r.list ?? []
    expect(list).toHaveLength(20)
    for (const id_ of list) expect(id_).toMatch(new RegExp(pattern))
    expect(new Set(list).size).toBe(20)
  })
  it('数量越界 → 引导文案', () => {
    expect(dev('interactive:uuid').compute!({ mode: 'uuid4', count: 51 })!.error).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// W4：JWT / .env / Markdown TOC / gitignore / 文本规范化 / 批量查找替换 / 密码生成
// ---------------------------------------------------------------------------
const w4 = (id: string) => getToolSchema(id)!

describe('JWT 解码 ↔ 黄金用例（不验签）', () => {
  it.each(golden.jwt.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = w4('interactive:jwt').compute!({ token: c.token })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows['alg']).toBe(c.expected.alg)
    expect(rows['exp（UTC）']).toBe(c.expected.exp)
    expect(rows['iat（UTC）']).toBe(c.expected.iat)
    expect(r.text).toBe(`${c.expected.header}\n\n${c.expected.payload}`)
  })
})

describe('.env 校验 ↔ 黄金用例', () => {
  it.each(golden.env.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = w4('interactive:env-check').compute!({ env: c.env, example: c.example })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows['缺失于 .env']).toBe(c.expected.missing.join(', ') || '无')
    expect(rows['多余于 .env']).toBe(c.expected.extra.join(', ') || '无')
    expect(rows['.env 空值键']).toBe(c.expected.empty.join(', ') || '无')
  })
})

describe('Markdown TOC ↔ 黄金用例', () => {
  it.each(golden.toc.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = w4('interactive:md-toc').compute!({ text: c.text, minLevel: c.minLevel, maxLevel: c.maxLevel })
    expect(r.primary?.value).toBe(c.expected.count)
    expect(r.text).toBe(c.expected.text)
  })
})

describe('gitignore 生成 ↔ 黄金用例', () => {
  const KEY_OF: Record<string, string> = {
    Python: 'py',
    Node: 'node',
    Go: 'go',
    macOS: 'mac',
    Windows: 'win',
    VSCode: 'vscode'
  }
  it.each(golden.gitignore.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const values = Object.fromEntries(c.stacks.map((s) => [KEY_OF[s]!, true]))
    const r = w4('interactive:gitignore').compute!(values)
    expect(r.text).toBe(c.expected.text)
  })
  it('全不选 → 引导文案', () => {
    expect(w4('interactive:gitignore').compute!({})!.error).toBeTruthy()
  })
})

describe('文本规范化 ↔ 黄金用例', () => {
  it.each(golden.normalize.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = w4('interactive:normalize').compute!({ text: c.text, lineEnding: c.lineEnding, indentMode: c.indentMode })
    expect(r.text).toBe(c.expected.text)
  })
})

describe('批量查找替换 ↔ 黄金用例', () => {
  it.each(golden.replacer.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = w4('interactive:find-replace').compute!({
      text: c.text,
      find: c.find,
      replace: c.replace,
      regex: c.regex,
      ignoreCase: c.ignoreCase
    })
    if ('error' in c.expected) {
      expect(r.error).toBeTruthy()
      return
    }
    expect(r.primary?.value).toBe(c.expected.count)
    expect(r.text).toBe(c.expected.text)
  })
})

describe('密码生成（随机型：字符集规则 + 包含性）', () => {
  const spec = golden.pwdgen
  it('长度与字符集符合所选范围', () => {
    const r = w4('interactive:pwd-gen').compute!({
      length: 24,
      lower: true,
      upper: true,
      digits: true,
      symbols: true,
      noAmbiguous: true
    })!
    const pwd = r.primary!.value
    expect(pwd).toHaveLength(24)
    expect(pwd.split('').every((c) => !spec.ambiguous.includes(c))).toBe(true)
    const allowed = [spec.lower, spec.upper, spec.digits, spec.symbols]
      .map((s) => s.split(''))
      .flat()
      .filter((c) => !spec.ambiguous.includes(c))
    expect(pwd.split('').every((c) => allowed.includes(c))).toBe(true)
  })
  it('每个所选字符集至少出现一个（构造保证）', () => {
    const r = w4('interactive:pwd-gen').compute!({
      length: 32,
      lower: true,
      upper: true,
      digits: true,
      symbols: true,
      noAmbiguous: false
    })!
    const pwd = r.primary!.value
    for (const pool of [spec.lower, spec.upper, spec.digits, spec.symbols]) {
      expect(pwd.split('').some((c) => pool.includes(c))).toBe(true)
    }
  })
  it('全不选字符集 → 引导文案', () => {
    expect(
      w4('interactive:pwd-gen').compute!({
        length: 16,
        lower: false,
        upper: false,
        digits: false,
        symbols: false,
        noAmbiguous: false
      })!.error
    ).toBeTruthy()
  })
  it('长度越界 → 引导文案', () => {
    expect(w4('interactive:pwd-gen').compute!({ length: 7, lower: true })!.error).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// W5：图片缩放试点（文件管道；compute 回显确定性，pyCode 真实执行在 pytest 侧）
// ---------------------------------------------------------------------------
describe('图片缩放 ↔ 黄金用例（参数回显）', () => {
  it.each(golden.image.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev('interactive:image-resize').compute!({ file: c.file, maxSide: c.maxSide, format: c.format })
    if ('error' in c.expected) {
      expect(r.error).toBe(c.expected.error)
      return
    }
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows).toEqual(c.expected.rows)
  })
  it('pyCode：源路径常量 + thumbnail 等比 + jpg 白底转换', () => {
    const schema = dev('interactive:image-resize')!
    const code = schema.pyCode!({ file: '/tmp/相 机.png', maxSide: 512, format: 'jpg' })
    expect(code).toContain('Image.open("/tmp/相 机.png")')
    expect(code).toContain('im.thumbnail((512, 512))')
    expect(code).toContain('im.convert("RGB")')
    expect(code).toContain('quality=90')
    expect(schema.pyCode!({ file: '', maxSide: 512, format: 'png' })).toContain('# 选择图片')
  })
})

// ---------------------------------------------------------------------------
// W6：B 档批量图片/Office（compute 回显抽测 + pyCode 关键片段全量）
// ---------------------------------------------------------------------------
describe('B 档工具 compute 回显 ↔ 黄金用例', () => {
  it.each(golden.filetools.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const r = dev(`interactive:${c.id}`).compute!(c.values)
    if ('error' in c.expected) {
      expect(r.error).toBe(c.expected.error)
      return
    }
    const rows = Object.fromEntries((r.rows ?? []).map((x) => [x.label, x.value]))
    expect(rows).toEqual(c.expected.rows)
  })
})

describe('B 档 pyCode 关键片段（PIL/openpyxl/pypdf 管线）', () => {
  const files: Record<string, string> = {
    'batch-resize': 'interactive:batch-resize',
    'batch-convert': 'interactive:batch-convert',
    'batch-crop': 'interactive:batch-crop',
    'batch-watermark': 'interactive:batch-watermark',
    palette: 'interactive:palette',
    'gif-extract': 'interactive:gif-extract',
    'gif-compose': 'interactive:gif-compose',
    'batch-enhance': 'interactive:batch-enhance',
    'rounded-frame': 'interactive:rounded-frame',
    'image-info': 'interactive:image-info',
    'excel-export': 'interactive:excel-export',
    'csv-excel': 'interactive:csv-excel',
    'pdf-extract': 'interactive:pdf-extract',
    'img-to-pdf': 'interactive:img-to-pdf'
  }
  const DIR = '/pics 空格'
  const FILE = '/单 词.png'

  it('批量四件套共享收集序章 + 逐图循环', () => {
    for (const id of ['batch-resize', 'batch-convert', 'batch-crop', 'batch-enhance']) {
      // 真实 UI 经 toolValueOf 注入字段默认值；这里带默认参数直调（水印记片段已单独覆盖 text 缺省路径）
      const code = dev(`interactive:${id}`).pyCode!({
        dir: DIR,
        maxSide: 1024,
        format: 'png',
        ratio: '1:1',
        brightness: 110,
        contrast: 110
      })
      expect(code, id).toContain('files = sorted(')
      expect(code, id).toContain(JSON.stringify(DIR))
      expect(code, id).toContain('for i, f in enumerate(files, 1):')
    }
  })
  it('水印：内置可缩放字体 + 平铺/右下角', () => {
    const code = dev('interactive:batch-watermark').pyCode!({ dir: DIR, text: '@ 我', position: 'tile', fontSize: 48 })
    expect(code).toContain('load_default(size=48)')
    expect(code).toContain('Image.alpha_composite')
    expect(code).toContain('"@ 我"')
  })
  it('GIF 系：帧计数与 save_all', () => {
    expect(dev('interactive:gif-extract').pyCode!({ file: FILE })).toContain('n_frames')
    const compose = dev('interactive:gif-compose').pyCode!({ dir: DIR, duration: 200, loop: 0 })
    expect(compose).toContain('save_all=True')
  })
  it('Office 系：openpyxl 读写与 pypdf 提取', () => {
    expect(dev('interactive:excel-export').pyCode!({ file: '/t.xlsx', sheet: '', format: 'json' })).toContain(
      'load_workbook'
    )
    expect(dev('interactive:csv-excel').pyCode!({ file: '/t.csv', sheet: 'S1' })).toContain('wb.save("converted.xlsx")')
    expect(dev('interactive:pdf-extract').pyCode!({ file: '/t.pdf', pages: 5 })).toContain(
      'from pypdf import PdfReader'
    )
    expect(dev('interactive:img-to-pdf').pyCode!({ dir: DIR })).toContain('save("out.pdf", save_all=True')
  })
  it('输入缺失 → 自播种示例数据（dir/file 型）或引导注释（office 系需用户文件）', () => {
    const SEED_IDS = new Set([
      'interactive:batch-resize',
      'interactive:batch-convert',
      'interactive:batch-crop',
      'interactive:batch-watermark',
      'interactive:palette',
      'interactive:gif-extract',
      'interactive:batch-enhance',
      'interactive:rounded-frame',
      'interactive:image-info',
      'interactive:gif-compose',
      'interactive:img-to-pdf'
    ])
    for (const [name, id] of Object.entries(files)) {
      // 与应用同口径：字段默认值参与（toolValueOf），空 dir/file 才触发自播种
      const values: Record<string, FieldValue> = { dir: '', file: '', text: '' }
      const spec0 = dev(id)
      const fields = typeof spec0.fields === 'function' ? spec0.fields({}) : spec0.fields
      for (const f of fields) if (f.default !== undefined) values[f.key] = f.default as FieldValue
      const code = dev(id).pyCode!(values)
      if (SEED_IDS.has(id)) {
        expect(code, name).toMatch(/_seed_sample_images|已自动生成示例图片/)
      } else {
        expect(code, name).toContain('# 选择')
      }
    }
  })
})

describe('缩略图拼贴', () => {
  it('pyCode：网格计算与格线', () => {
    const code = dev('interactive:contact-sheet').pyCode!({ dir: '/pics', cols: 4, cell: 200, bg: '#111111' })
    expect(code).toContain('CELL, COLS = 200, 4')
    expect(code).toContain('sheet.save("contact_sheet.png")')
    const seeded = dev('interactive:contact-sheet').pyCode!({ dir: '', cols: 4, cell: 200, bg: '#111111' })
    expect(seeded).toContain('CELL, COLS = 200, 4')
    expect(seeded).toMatch(/_seed_sample_images|已自动生成示例图片/)
  })
})

// ---------------------------------------------------------------------------
// W8-W11：速查/结果浏览/向导/ffmpeg 构建器（sidecar 计算型：pyCode 关键片段全量钉）
// ---------------------------------------------------------------------------
const FRAGMENTS: Array<[string, Record<string, FieldValue>, string[]]> = [
  ['ip-lookup', {}, ['ipify', 'ipinfo', '<<<JSON>>>']],
  ['dns-lookup', { domain: 'example.com' }, ['getaddrinfo', '"example.com"']],
  ['port-check', { host: '127.0.0.1', port: 80 }, ['connect_ex', '"127.0.0.1:80"']],
  ['http-headers', { url: 'https://example.com' }, ['requests.get', 'status_code']],
  ['speed-test', {}, ['httpbin.org/bytes', 'MB/s 均值']],
  ['battery', {}, ['sensors_battery', 'power_plugged']],
  ['disk-usage', {}, ['disk_usage', '/Volumes/Data']],
  ['system-info', {}, ['platform.release()', 'os.cpu_count()']],
  ['process-top', {}, ['process_iter', 'memory_info']],
  ['media-info', { file: '/m.mp4' }, ['ffprobe', '"-show_streams"']],
  ['bigfile-topn', { dir: '/data', top: 5 }, ['rglob("*")', 'files[:5]']],
  ['dup-finder', { dir: '/data' }, ['md5', 'len(paths) > 1']],
  ['empty-dir', { dir: '/data' }, ['空目录', 'not any(p.iterdir())']],
  ['dir-size', { dir: '/data' }, ['tree_size', 'entries.sort']],
  ['quick-find', { dir: '/data', pattern: 'report.*xlsx' }, ["re.compile(r'''report.*xlsx'''", 'pat.search']],
  ['tree-print', { dir: '/data', depth: 2 }, ['IGNORE', 'walk(']],
  ['todo-scan', { dir: '/code' }, ['TODO|FIXME|HACK', 'exts']],
  ['secret-scan', { dir: '/code' }, ['api[_-]?key', '***']],
  ['loc-stats', { dir: '/code' }, ['startswith', '代码行']],
  ['csv-column-stats', { file: '/t.csv', column: 'age' }, ['DictReader', '均值']],
  ['log-level-stats', { file: '/a.log' }, ['TRACE|DEBUG|INFO', 'most_common']],
  ['git-branches', { dir: '/repo' }, ['rev-parse', '--abbrev-ref']],
  ['git-commits', { dir: '/repo' }, ['--numstat', '%an']],
  ['table-diff', { oldFile: '/o.xlsx', newFile: '/n.xlsx', keyCol: '工号' }, ['sheet_rows', '"工号"', 'added']],
  ['sheet-split', { file: '/w.xlsx' }, ['sheetnames', 'max_row']],
  ['dedup-merge', { fileA: '/a.xlsx', fileB: '/b.xlsx', keyCol: '工号' }, ['A 覆盖 B', '唯一记录']],
  ['batch-rename', { dir: '/f', prefix: 'pic', apply: false }, ['预览模式', 'plan =']],
  ['file-classify', { dir: '/f', apply: true }, ['shutil.move', '已归类']],
  ['sqlite-export', { db: '/d.sqlite', table: 'orders' }, ['sqlite3.connect', 'SELECT * FROM']],
  ['video-compress', { file: '/v.mp4', crf: 24, preset: 'slow' }, ['libx264', '"-crf", "24"', '"slow"']],
  ['video-convert', { file: '/v.mp4', format: 'webm' }, ['libvpx-vp9', 'converted.webm']],
  ['video-merge', { dir: '/vids' }, ['concat', 'parts.txt']],
  ['video-to-gif', { file: '/v.mp4', start: 1, dur: 4, fps: 10, width: 320 }, ['palettegen', 'fps=10']],
  ['video-shot', { file: '/v.mp4', at: 5 }, ['-frames:v', '1', 'shot.png']],
  ['remove-audio', { file: '/v.mp4' }, ['-an', 'muted.mp4']],
  ['av-trim', { file: '/v.mp4', start: 2, dur: 15 }, ['-ss', '-c', 'copy']],
  ['volume-adjust', { file: '/v.mp4', vol: 2 }, ['volume=', 'adjusted.mp4']],
  ['extract-audio', { file: '/v.mp4' }, ['-vn', 'libmp3lame']],
  ['audio-compress', { file: '/a.wav', format: 'mp3', bitrate: 192 }, ['libmp3lame', '"192k"']],
  ['batch-transcode', { dir: '/vids', crf: 28 }, ['transcoded_', '成功/总数', '<<<JSON>>>']]
]

describe('W8-W11 四十工具 pyCode ↔ 关键片段', () => {
  it.each(FRAGMENTS.map(([id, values, frags]) => [id, values, frags] as const))('%s', (id, values, frags) => {
    const schema = dev(`interactive:${id}`)!
    expect(schema, id).toBeTruthy()
    expect(schema.computeVia, id).toBe('sidecar')
    const code = schema.pyCode!(values)
    for (const f of frags) expect(code, `${id} 应含 ${f}`).toContain(f)
    // 统一契约：结果 JSON 标记
    expect(code, `${id} 应含结果标记`).toContain('<<<JSON>>>')
    expect(code, `${id} 应含结束标记`).toContain('<<<END>>>')
  })
  it('向导六件都声明 steps；速查本地件声明 quickRun', () => {
    expect(dev('interactive:table-diff')!.steps).toHaveLength(2)
    expect(dev('interactive:sqlite-export')!.steps).toHaveLength(2)
    expect(dev('interactive:battery')!.quickRun).toBe(true)
    expect(dev('interactive:speed-test')!.quickRun).toBeUndefined()
    expect(dev('interactive:video-compress')!.quickRun).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// W12 收官批：Office 改造 + 字符方阵/文本表格 + 监控（21 schema 片段表）
// ---------------------------------------------------------------------------
const W12_FRAGMENTS: Array<[string, Record<string, FieldValue>, string[]]> = [
  ['char-matrix', { size: 9, chars: '◆◇' }, ['size, chars = 9', 'r * c + r + c']],
  ['text-table', { data: '名称,数量' }, ['ljust', 'widths']],
  ['site-monitor', { urls: 'https://a.com' }, ['requests.get', '可用']],
  ['file-watch', { dir: '/w', interval: 5 }, ['两次快照', 'time.sleep(5)']],
  ['excel-build', { data: '名称,数量\n苹果,12' }, ['_coerce', 'output.xlsx']],
  ['excel-style', { data: 'A,B' }, ['PatternFill', 'Font(bold=True']],
  ['excel-formula', { data: 'A,B' }, ['SUM(', 'get_column_letter']],
  ['excel-chart', { data: 'A,B' }, ['BarChart', 'add_chart']],
  ['excel-freeze', { data: 'A,B' }, ['freeze_panes = "A2"']],
  ['excel-condfmt', { data: 'A,B' }, ['DataBarRule', 'conditional_formatting']],
  ['excel-sort', { data: 'A,B' }, ['body.sort', 'ws.append(r)']],
  ['excel-protect', { data: 'A,B', password: 'pw' }, ['protection.password', 'sheet = True']],
  ['excel-comment', { data: 'A,B' }, ['Comment(', 'PyCase']],
  ['excel-merge-header', { data: 'A,B' }, ['merge_cells', 'insert_rows']],
  ['word-doc', { content: '# 标题\n正文' }, ['add_heading', 'List Bullet']],
  ['word-table', { data: 'A,B' }, ['Table Grid', 'add_table']],
  ['word-letters', { template: '尊敬的{{姓名}}', data: '姓名\n张三' }, ['DictReader', 'letter_']],
  ['ppt-slides', { slides: '封面|我的演示' }, ['Presentation', 'add_slide']],
  ['daily-report', { done: '写代码', plan: '改 bug', issues: '无' }, ['今日完成', '明日计划', '问题与风险']],
  ['md-todo', { items: '任务 @张三 !P0' }, ['- [ ]', 'P\\d']],
  ['mail-draft', { to: 'a@b.c', subject: 'S', body: 'B' }, ['MIMEText', 'draft.eml']]
]

describe('W12 廿一工具 pyCode ↔ 关键片段', () => {
  it.each(W12_FRAGMENTS.map(([id, values, frags]) => [id, values, frags] as const))('%s', (id, values, frags) => {
    const schema = dev(`interactive:${id}`)!
    expect(schema, id).toBeTruthy()
    const code = schema.pyCode!(values)
    for (const f of frags) expect(code, `${id} 应含 ${f}`).toContain(f)
  })
  it('纯前端两件不走 sidecar', () => {
    expect(dev('interactive:char-matrix')!.computeVia).toBeUndefined()
    expect(dev('interactive:text-table')!.computeVia).toBeUndefined()
  })
  it('字符方阵 compute：纹理解析与边界', () => {
    const r = dev('interactive:char-matrix').compute!({ size: 5, chars: 'AB' })
    const lines = r.text!.split('\n')
    expect(lines).toHaveLength(5)
    expect(lines[0]!.length).toBe(5)
    expect(dev('interactive:char-matrix').compute!({ size: 3, chars: 'AB' })!.error).toContain('边长')
  })
  it('文本表格 compute：对齐输出', () => {
    const r = dev('interactive:text-table').compute!({ data: '名称,数量\n苹果,12' })
    expect(r.text).toContain('| 名称 | 数量 |')
    expect(r.primary?.value).toBe('1')
  })
})

// ---------------------------------------------------------------------------
// W13 增补批 ×10：YAML/Base64/URL/文本对比/二维码/编码修复/透视/跨表关联/数据校验/库存盘点
// ---------------------------------------------------------------------------
const W13_FRAGMENTS: Array<[string, Record<string, FieldValue>, string[]]> = [
  ['yaml-json', { direction: 'yaml2json', input: 'a: 1' }, ['safe_load', 'ensure_ascii=False']],
  ['base64', { mode: 'encode', input: 'Hello' }, ['b64encode', 'utf-8']],
  ['url-codec', { mode: 'encode', input: '中文' }, ['quote(', 'safe=""']],
  ['text-diff', { before: 'a', after: 'b' }, ['difflib', 'unified_diff']],
  ['qrcode-gen', { text: 'https://example.com' }, ['qrcode.make', 'qrcode.png']],
  ['encoding-fix', { file: '/t.txt' }, ['gbk', 'latin-1', 'fixed.utf8.txt']],
  [
    'pivot',
    { data: '部门,月份,金额', rowDim: '部门', colDim: '月份', valCol: '金额' },
    ['defaultdict(float)', 'colKeys']
  ],
  [
    'cross-join',
    { mainFile: '/m.xlsx', lookupFile: '/l.xlsx', mainKey: '工号', lookupKey: '工号', lookupVal: '姓名' },
    ['左连接', '<未知>']
  ],
  ['data-validate', { data: '日期,工时\nA,8', col: '工时', min: 0, max: 16, allowEmpty: true }, ['空值放行', '超范围']],
  ['stock-inventory', { opening: '键盘,12', inflow: '键盘,10', outflow: '鼠标,15' }, ['defaultdict', '需补货']]
]

describe('W13 十工具 pyCode ↔ 关键片段', () => {
  it.each(W13_FRAGMENTS.map(([id, values, frags]) => [id, values, frags] as const))('%s', (id, values, frags) => {
    const schema = dev(`interactive:${id}`)!
    expect(schema, id).toBeTruthy()
    const code = schema.pyCode!(values)
    for (const f of frags) expect(code, `${id} 应含 ${f}`).toContain(f)
  })
  it('纯前端三件不走 sidecar', () => {
    expect(dev('interactive:base64')!.computeVia).toBeUndefined()
    expect(dev('interactive:url-codec')!.computeVia).toBeUndefined()
    expect(dev('interactive:stock-inventory')!.computeVia).toBeUndefined()
  })
  it('base64 前端编解码：中文 UTF-8 安全', () => {
    const enc = dev('interactive:base64').compute!({ mode: 'encode', input: '中文Hello' })
    const dec = dev('interactive:base64').compute!({ mode: 'decode', input: enc.text! })
    expect(dec.text).toBe('中文Hello')
  })
  it('库存盘点 compute：三表核算与补货标记', () => {
    const r = dev('interactive:stock-inventory').compute!({
      opening: '键盘,12\n鼠标,30',
      inflow: '键盘,10',
      outflow: '鼠标,15\n显示器,2'
    })!
    const rows = Object.fromEntries(r.table!.rows.map((x) => [x[0], x[1]]))
    expect(rows['键盘']).toBe('22')
    expect(rows['鼠标']).toBe('15')
    expect(rows['显示器']).toBe('-2') // 无期初直接出库 → 负数（defaultdict 语义）
    expect(r.table!.rows.find((x) => x[0] === '显示器')![2]).toContain('需补货')
  })
})

// ---------------------------------------------------------------------------
// W15 终极补齐 ×4：保险库写入/查看、一次性定时任务、Word 读取
// ---------------------------------------------------------------------------
const W15_FRAGMENTS: Array<[string, Record<string, FieldValue>, string[]]> = [
  ['vault-add', { master: 'm1', site: 'github.com', secret: 's3cret' }, ['keystream', '已保存', '<<<JSON>>>']],
  ['vault-list', { master: 'm1' }, ['load(', '<<<JSON>>>']],
  ['sched-once', { delay: 5, task: "print('任务')" }, ['sched.scheduler', 'scheduler.enter(5', '<<<JSON>>>']],
  ['word-read', { file: '/周会.docx' }, ['doc.paragraphs', 'doc.tables', '<<<JSON>>>']]
]

describe('W15 四工具 pyCode ↔ 关键片段', () => {
  it.each(W15_FRAGMENTS.map(([id, values, frags]) => [id, values, frags] as const))('%s', (id, values, frags) => {
    const schema = dev(`interactive:${id}`)!
    expect(schema, id).toBeTruthy()
    expect(schema.computeVia, id).toBe('sidecar')
    const code = schema.pyCode!(values)
    for (const f of frags) expect(code, `${id} 应含 ${f}`).toContain(f)
  })
  it('password 字段类型存在且 vaultList 单步', () => {
    const vaultFields = dev('interactive:vault-add')!.fields
    expect((Array.isArray(vaultFields) ? vaultFields : vaultFields({}))[0]!.type).toBe('password')
    expect(dev('interactive:vault-list')!.steps).toBeUndefined()
    expect(dev('interactive:vault-add')!.steps).toHaveLength(2)
  })
})
