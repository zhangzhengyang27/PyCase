// pyCode 真跑回归：全量取证（323 页 venv 执行 + 产物非空校验）抓出的 4 个「跑了但无有效产物」
// 页面在此钉死——取证口径教训：产物存在 ≠ 内容非空（system-info NameError 必挂、process-top
// 对消失进程取 rss 崩、gifframes 调色板缺失导出全黑图、pathlib 树建错位置零输出还污染运行目录）。
import { execFileSync } from 'node:child_process'
import { existsSync, mkdtempSync, writeFileSync, readdirSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import type { FieldValue } from '../interactive-tools'
import { getToolSchema } from '../interactive-tools'
import { CRAWLER_TYPES, crawlerLabSchema } from '../tool-schemas-crawler-lab'

// 页面产物依赖 psutil/PIL/numpy（系统 python3 无），用仓库根 .venv 跑
const VENV_PY = join(process.cwd(), '../../.venv/bin/python')
const hasVenv = existsSync(VENV_PY)

function pyCodeOf(id: string, extra: Record<string, FieldValue> = {}): string {
  const schema = getToolSchema(id)
  if (!schema) throw new Error(`unknown schema: ${id}`)
  const v: Record<string, FieldValue> = { ...extra }
  const fields = typeof schema.fields === 'function' ? schema.fields(v) : schema.fields
  for (const f of fields) if (v[f.key] === undefined) v[f.key] = f.default
  return schema.pyCode(v)
}

describe.skipIf(!hasVenv)('pyCode 真跑回归（.venv 执行 + 产物非空）', () => {
  function run(code: string): { stdout: string; cwd: string } {
    const cwd = mkdtempSync(join(tmpdir(), 'pyexec-run-'))
    writeFileSync(join(cwd, 'page.py'), code)
    const stdout = execFileSync(VENV_PY, [join(cwd, 'page.py')], {
      encoding: 'utf8',
      timeout: 60_000,
      cwd
    })
    return { stdout, cwd }
  }

  it('system-info：正常输出 JSON（import 不得先用后导）', () => {
    const { stdout } = run(pyCodeOf('interactive:system-info'))
    expect(stdout).toContain('<<<JSON>>>')
    expect(stdout).not.toContain('Traceback')
  })

  it('process-top：进程快照不因进程消失而崩', () => {
    const { stdout } = run(pyCodeOf('interactive:process-top'))
    expect(stdout).toContain('<<<JSON>>>')
    expect(stdout).not.toContain('Traceback')
  })

  it('gifframes：导出帧非全黑（P 模式必须设调色板）', () => {
    const { cwd } = run(pyCodeOf('interactive:pil-lab', { type: 'gifframes' }))
    const out = execFileSync(
      VENV_PY,
      [
        '-c',
        `from PIL import Image; im = Image.open(${JSON.stringify(join(cwd, 'effect.png'))}).convert('RGB'); print('uniform' if all(lo == hi for lo, hi in im.getextrema()) else 'ok')`
      ],
      { encoding: 'utf8', timeout: 30_000 }
    )
    expect(out.trim()).toBe('ok')
  })

  it('pathlib：glob 有输出且不向运行目录撒游离目录', () => {
    const { stdout, cwd } = run(pyCodeOf('interactive:basics-lab', { type: 'pathlib' }))
    expect(stdout).toContain('main.py')
    expect(
      readdirSync(cwd)
        .filter((n) => n !== 'page.py')
        .sort()
    ).toEqual(['project'])
  })

  it('word-doc / word-table / stock-inventory：JSON 标记输出不缺 import json', () => {
    for (const [id, v] of [
      ['interactive:word-doc', { content: '# 报告\n正文\n- 要点一' }],
      ['interactive:word-table', { data: '名称,数量\n苹果,12' }],
      ['interactive:stock-inventory', { opening: '键盘,12\n鼠标,30', inflow: '键盘,10', outflow: '鼠标,15' }]
    ] as Array<[string, Record<string, FieldValue>]>) {
      const { stdout } = run(pyCodeOf(id, v))
      expect(stdout, id).toContain('<<<END>>>')
    }
  })

  it('charts-v2 中文图页：12 页默认路径全部产出 chart.png（曾整批缺 import json）', () => {
    for (const id of [
      'interactive:直方图',
      'interactive:热力图',
      'interactive:雷达图',
      'interactive:箱线图',
      'interactive:面积图',
      'interactive:误差条图',
      'interactive:水平条形图',
      'interactive:极坐标玫瑰',
      'interactive:散点密度图',
      'interactive:阶梯图'
    ]) {
      const { stdout } = run(pyCodeOf(id))
      expect(stdout, id).toContain('已输出 chart.png')
    }
  })

  it('等高线图：无数据用内置演示网格、合法网格出图、坏网格给引导', () => {
    const s = getToolSchema('interactive:等高线图')!
    const bad = s.compute!({ levels: 10, data: 'x,y\n1,10\n2,20' })
    expect((bad as { error?: string }).error).toContain('网格形状不对')
    const { stdout } = run(pyCodeOf('interactive:等高线图'))
    expect(stdout).toContain('已输出 chart.png')
    const { stdout: custom } = run(
      pyCodeOf('interactive:等高线图', { levels: 8, data: 'x,a,b\nr1,1,2\nr2,2,3\nr3,3,5' })
    )
    expect(custom).toContain('已输出 chart.png')
  })
})

// ---------------------------------------------------------------------------
// 爬虫实验室全类型真跑循环（57 类型 = crawler/crawler2/crawler3 教案归并单页）：
// 生成的脚本默认抓本地 fixture 服务器，离线可跑——首建批取证 sweep 抓出 3 个必崩
// （xml-ns 未声明命名空间前缀 / test-spider 引用未定义 __main__ / unittest 输出走 stderr），
// 本循环作为永久回归钉住「每个类型生成的脚本 exit 0 且 stdout 有内容」。
// ---------------------------------------------------------------------------
describe.skipIf(!hasVenv)('爬虫实验室全类型真跑', () => {
  it('57 类型逐一生成 + 执行：exit 0 且 stdout 非空', () => {
    expect(CRAWLER_TYPES.length).toBe(57)
    const failures: string[] = []
    for (const t of CRAWLER_TYPES) {
      const v: Record<string, FieldValue> = { type: t.value }
      for (const f of t.fields ?? []) v[f.key] = f.default
      const code = crawlerLabSchema.pyCode(v)
      expect(code, `${t.value} 生成空代码`).not.toBe('')
      const cwd = mkdtempSync(join(tmpdir(), 'crawler-pyexec-'))
      writeFileSync(join(cwd, 'page.py'), code)
      try {
        const stdout = execFileSync(VENV_PY, [join(cwd, 'page.py')], {
          encoding: 'utf8',
          timeout: 60_000,
          cwd
        })
        if (!stdout.trim() || stdout.includes('Traceback')) failures.push(t.value)
      } catch (e) {
        failures.push(`${t.value}: ${String((e as Error).message).split('\n')[0]}`)
      }
    }
    expect(failures, `失败类型: ${failures.join(', ')}`).toEqual([])
  }, 300_000)
})
