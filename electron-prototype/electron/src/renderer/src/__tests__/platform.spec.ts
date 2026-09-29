// 平台适配层测试：平台探测、修饰键标签、窗口三键适配（B3-2）。
//
// 平台来自 preload 写入的 html[data-platform]；组件只认 src/platform.ts，
// 不自行判断平台、也不直接摸 window.sidecar（窗口控制的依赖由 createWindowControls 注入）。
import { afterEach, describe, expect, it, vi } from 'vitest'

import { createWindowControls, currentPlatform, modKeyLabel, showsWindowControls } from '../platform'

function setPlatform(value: 'mac' | 'win' | null): void {
  if (value === null) document.documentElement.removeAttribute('data-platform')
  else document.documentElement.setAttribute('data-platform', value)
}

afterEach(() => setPlatform(null))

describe('平台探测与文案', () => {
  it('data-platform=win → win，其余（含缺省）回退 mac', () => {
    setPlatform('win')
    expect(currentPlatform()).toBe('win')
    setPlatform('mac')
    expect(currentPlatform()).toBe('mac')
    setPlatform(null)
    expect(currentPlatform()).toBe('mac')
  })

  it('修饰键标签随平台切换', () => {
    setPlatform('mac')
    expect(modKeyLabel()).toBe('⌘')
    setPlatform('win')
    expect(modKeyLabel()).toBe('Ctrl')
  })

  it('自绘标题栏三键只在 win 展示（mac 用原生红绿灯）', () => {
    setPlatform('win')
    expect(showsWindowControls()).toBe(true)
    setPlatform('mac')
    expect(showsWindowControls()).toBe(false)
  })
})

describe('窗口控制适配（createWindowControls）', () => {
  function makeDeps() {
    return {
      minimize: vi.fn(async () => undefined),
      toggleMaximize: vi.fn(async () => true),
      close: vi.fn(async () => undefined),
      isMaximized: vi.fn(async () => false),
      onMaximized: vi.fn((fn: (v: boolean) => void) => {
        fn(true)
        return () => {}
      })
    }
  }

  it('三键委托给注入的实现', async () => {
    const deps = makeDeps()
    const wc = createWindowControls(deps)
    wc.minimize()
    expect(await wc.toggleMaximize()).toBe(true)
    wc.close()
    expect(deps.minimize).toHaveBeenCalledTimes(1)
    expect(deps.toggleMaximize).toHaveBeenCalledTimes(1)
    expect(deps.close).toHaveBeenCalledTimes(1)
  })

  it('最大化状态变化经适配层透传（布尔化）', () => {
    const deps = makeDeps()
    const seen: boolean[] = []
    createWindowControls(deps).onMaximizedChange((v) => seen.push(v))
    expect(seen).toEqual([true])
  })

  it('IPC 失败不抛出：最小化/关闭吞错，最大化/查询回退 false', async () => {
    const wc = createWindowControls({
      minimize: async () => {
        throw new Error('ipc down')
      },
      toggleMaximize: async () => {
        throw new Error('ipc down')
      },
      close: async () => {
        throw new Error('ipc down')
      },
      isMaximized: async () => {
        throw new Error('ipc down')
      },
      onMaximized: () => () => {}
    })
    expect(() => wc.minimize()).not.toThrow()
    expect(() => wc.close()).not.toThrow()
    expect(await wc.toggleMaximize()).toBe(false)
    expect(await wc.isMaximized()).toBe(false)
  })
})
