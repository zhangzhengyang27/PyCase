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
      ['-c', `from PIL import Image; im = Image.open(${JSON.stringify(join(cwd, 'effect.png'))}).convert('RGB'); print('uniform' if all(lo == hi for lo, hi in im.getextrema()) else 'ok')`],
      { encoding: 'utf8', timeout: 30_000 }
    )
    expect(out.trim()).toBe('ok')
  })

  it('pathlib：glob 有输出且不向运行目录撒游离目录', () => {
    const { stdout, cwd } = run(pyCodeOf('interactive:basics-lab', { type: 'pathlib' }))
    expect(stdout).toContain('main.py')
    expect(readdirSync(cwd).filter((n) => n !== 'page.py').sort()).toEqual(['project'])
  })
})
