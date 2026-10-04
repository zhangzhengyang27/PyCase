// turtle-lab 真跑取证：生成代码必须在 Tk 画布上真实落笔（画布 line 端点数验证）。
// 背景：T 子类把 goto 覆写为瞬移，靠 goto 逐点连线的曲线族曾整窗空白——
// b81b3f8 的「补 pendown」修复被覆写击败，而「超时阻塞 + stderr 干净」的取证口径
// 验不出空窗。这里真跑生成的 pyCode 数端点：空窗是个位数（pendown 的零长度线），
// 画出曲线是数百上千端点，阈值两侧都留了量级余量。其余 25 族靠 forward 画线，
// 语义不同，不在本用例范围。
import { execFileSync } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { beforeAll, describe, expect, it } from 'vitest'
import type { FieldValue } from '../interactive-tools'
import { TURTLE_SHAPES, turtleLabSchema } from '../tool-schemas-turtle'

// 静音取证 harness：吞掉 turtle.done 的 mainloop、关动画、撤掉窗口（无闪窗），
// exec 生成代码后数画布上所有 line 图元的端点数。
const HARNESS = `\
import sys, turtle

turtle.done = lambda: None
_real_screen = turtle.Screen

def _quiet_screen():
    s = _real_screen()
    s.tracer(0)
    s.getcanvas().winfo_toplevel().withdraw()
    return s

turtle.Screen = _quiet_screen

path = sys.argv[1]
exec(compile(open(path).read(), path, "exec"), {"__name__": "__main__"})

cv = turtle.getcanvas()
print(sum(len(cv.coords(i)) // 2 for i in cv.find_all() if cv.type(i) == "line"))
`

// 图像主体是逐点连线的曲线族：端点数 ≈ 采样段数（默认参数下 601/301/901/2413），
// 阈值取预期的一半，坏实现（个位数零长度端点）与好实现之间隔着量级。
const CURVE_FAMILIES: Array<{ value: string; minEndpoints: number }> = [
  { value: 'lissajous', minEndpoints: 300 },
  { value: 'heart', minEndpoints: 150 },
  { value: 'butterfly', minEndpoints: 450 },
  { value: 'waves', minEndpoints: 1200 }
]

function pyCodeOf(value: string): string {
  const family = TURTLE_SHAPES.find((f) => f.value === value)
  if (!family) throw new Error(`unknown turtle family: ${value}`)
  const v: Record<string, FieldValue> = { type: family.value, palette: 'rainbow' }
  for (const field of family.fields) v[field.key] = field.default
  return turtleLabSchema.pyCode!(v)
}

const hasTurtlePython = (() => {
  try {
    execFileSync('python3', ['-c', 'import tkinter'], { stdio: 'ignore' })
    return true
  } catch {
    return false
  }
})()

describe.skipIf(!hasTurtlePython)('turtle-lab 曲线族真跑取证（画布 line 端点数）', () => {
  let dir: string
  beforeAll(() => {
    dir = mkdtempSync(join(tmpdir(), 'turtle-lab-canvas-'))
    writeFileSync(join(dir, 'harness.py'), HARNESS)
  })

  for (const { value, minEndpoints } of CURVE_FAMILIES) {
    it(
      `${value}: 落笔端点 ≥ ${minEndpoints}`,
      () => {
        const codePath = join(dir, `${value}.py`)
        writeFileSync(codePath, pyCodeOf(value))
        const out = execFileSync('python3', [join(dir, 'harness.py'), codePath], {
          encoding: 'utf8',
          timeout: 60_000
        })
        expect(Number(out.trim())).toBeGreaterThanOrEqual(minEndpoints)
      },
      90_000
    )
  }
})
