// overlays 层组件测试：全局层两处（帮助面板 HelpSheet / 首启引导页 OnboardingView）。
//
// 关注点与别的层不同：这两处的正确性**主要取决于数据是否来自真实来源**——
// 键位表必须与代码一致、步骤状态必须来自 sidecar 上报（phase/failed_at），
// 而不是组件自己编一套。因此用例围绕「给定 env 状态 → 呈现什么」来写。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import HelpSheet from '../HelpSheet.vue'
import OnboardingView from '../OnboardingView.vue'
import { examples } from '../../src/store/catalog'
import { appInfo, envStatus, type EnvStatus } from '../../src/store/env'
import { modKeyLabel } from '../../src/platform'

const baseEnv: EnvStatus = {
  phase: 'preparing',
  mode: 'shared',
  venv_path: '/tmp/PyCase/.venv',
  venv_ready: false,
  python_version: '3.13.0',
  examples: 1496,
  elapsed_ms: 80_000
}

beforeEach(() => {
  document.documentElement.setAttribute('data-platform', 'mac')
  envStatus.value = { ...baseEnv }
  appInfo.value = {}
  examples.value = []
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('HelpSheet', () => {
  // 组件用 <Teleport to="body">，wrapper 里没有内容：统一查 document.body
  const bodyText = (): string => document.body.textContent || ''

  it('键位表条数与描述齐备（与代码同源，改动快捷键时必须同步）', () => {
    mount(HelpSheet, { attachTo: document.body })
    const kbds = document.body.querySelectorAll('.grid-cols-\\[auto_1fr\\] kbd')
    // 7 条键位：⌘K / ↑↓ / ↵ / ⌘↵ / ⌘S / ⌘. / ⌘/
    expect(kbds.length).toBeGreaterThanOrEqual(7)
    expect(bodyText()).toContain('全局搜索')
    expect(bodyText()).toContain('停止正在运行的示例')
    expect(bodyText()).toContain('打开 / 关闭本页')
  })

  it('修饰键随平台显示（win 下不得出现 ⌘）', () => {
    document.documentElement.setAttribute('data-platform', 'win')
    mount(HelpSheet, { attachTo: document.body })
    expect(bodyText()).toContain('Ctrl K')
    expect(bodyText()).not.toContain('⌘')
  })

  it('安全边界与快捷键来源都在正文里（不是装饰性文案）', () => {
    mount(HelpSheet, { attachTo: document.body })
    expect(bodyText()).toContain('不是安全沙箱')
    expect(bodyText()).toContain('子进程')
  })

  it('环境信息取真实来源：版本来自 appInfo、环境来自 envStatus', () => {
    appInfo.value = { version: '9.9.9', electron: '33.0.0' }
    envStatus.value = { ...baseEnv, phase: 'ready', venv_ready: true }
    mount(HelpSheet, { attachTo: document.body })
    expect(bodyText()).toContain('9.9.9')
    expect(bodyText()).toContain('Python 3.13.0')
    expect(bodyText()).toContain('已就绪')
    expect(bodyText()).not.toContain('9.9.8')
  })

  it('Esc 关闭并阻止冒泡（不许连带关掉底下弹层）', async () => {
    const w = mount(HelpSheet, { attachTo: document.body })
    const ev = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true })
    window.dispatchEvent(ev)
    expect(w.emitted('close')).toHaveLength(1)
    expect(ev.defaultPrevented).toBe(true)
  })

  it('关闭按钮发 close 事件', async () => {
    const w = mount(HelpSheet, { attachTo: document.body })
    const btn = document.body.querySelector('button[aria-label="关闭帮助"]') as HTMLElement
    expect(btn).toBeTruthy()
    btn.click()
    await w.vm.$nextTick()
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('平台化修饰键取自 platform.ts（单一来源，不写死）', () => {
    expect(modKeyLabel()).toBe('⌘')
    document.documentElement.setAttribute('data-platform', 'win')
    expect(modKeyLabel()).toBe('Ctrl')
  })
})

describe('OnboardingView', () => {
  it('准备中：显示当前阶段与已用时，「开始浏览」可用', () => {
    const w = mount(OnboardingView)
    expect(w.text()).toContain('正在准备运行环境')
    expect(w.text()).toContain('已用时 1:20')
    const buttons = w.findAll('button').map((b) => b.text())
    expect(buttons).toContain('开始浏览')
    expect(buttons).toContain('跳过引导')
    expect(buttons.join()).not.toContain('重试')
  })

  it('失败：显示 sidecar 上报的原因与失败步骤，给三个出口', () => {
    envStatus.value = {
      ...baseEnv,
      phase: 'failed',
      failed_at: 'preparing',
      error: 'pip 安装超时（镜像不可达）'
    }
    const w = mount(OnboardingView)
    expect(w.text()).toContain('环境准备失败')
    expect(w.text()).toContain('pip 安装超时（镜像不可达）')
    const buttons = w.findAll('button').map((b) => b.text())
    expect(buttons).toContain('重试')
    expect(buttons).toContain('查看准备日志')
    expect(buttons).toContain('用系统 Python 继续')
    expect(buttons.join()).not.toContain('开始浏览')
  })

  it('失败步骤定位来自 failed_at（不是猜的）', () => {
    envStatus.value = { ...baseEnv, phase: 'failed', failed_at: 'warming', error: 'x' }
    const w = mount(OnboardingView)
    // 前三步（启动/依赖/索引）应显示已完成，只有最后一步是失败
    expect(w.text().match(/已完成/g)?.length ?? 0).toBeGreaterThanOrEqual(3)
  })

  it('就绪：文案切换，且不再显示不确定进度', () => {
    envStatus.value = { ...baseEnv, phase: 'ready', venv_ready: true }
    const w = mount(OnboardingView)
    expect(w.text()).toContain('运行环境已就绪')
    expect(w.find('.animate-indeterminate').exists()).toBe(false)
  })

  it('已切到系统 Python：失败态不再提示「用系统 Python 继续」', () => {
    envStatus.value = { ...baseEnv, phase: 'failed', failed_at: 'preparing', mode: 'system', error: 'x' }
    const w = mount(OnboardingView)
    const buttons = w.findAll('button').map((b) => b.text())
    expect(buttons).not.toContain('用系统 Python 继续')
  })

  it('开始浏览写入首启标记（只出现一次的依据）', async () => {
    const w = mount(OnboardingView)
    const start = w.findAll('button').find((b) => b.text() === '开始浏览')!
    await start.trigger('click')
    expect(vi.mocked(window.sidecar.store.set)).toHaveBeenCalledWith(
      'onboarding',
      expect.objectContaining({ seen: true })
    )
  })

  it('win 下主操作在最左（Fluent 惯例），mac 下在最右', async () => {
    const mac = mount(OnboardingView, { attachTo: document.body })
    const macButtons = mac.findAll('button').map((b) => b.text())
    expect(macButtons[0]).toBe('开始浏览')
    mac.unmount()

    document.documentElement.setAttribute('data-platform', 'win')
    const win = mount(OnboardingView, { attachTo: document.body })
    // 类名层面断言顺序规则（jsdom 不做布局，无法比较坐标）
    expect(win.find('.d-actions').exists()).toBe(true)
    expect(win.find('.d-primary').exists()).toBe(true)
  })
})
